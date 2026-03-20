from __future__ import annotations
from json import tool
import tkinter as tk
from typing import Callable, Optional
from PIL import Image, ImageTk
from click import command
from httpx import delete
from numpy import double
import scipy as sp
from sympy import false, true

from invoices_generator.core.enumerates.segment_tags import segment_tags
from invoice_annotator.enumerates.ContextMenuOptions import ContextMenuOptions
from invoice_annotator.AppData import AppData
from invoice_annotator.enumerates.DataSource import DataSource
from invoice_annotator.enumerates.EventSource import EventSource
from invoice_annotator.utils.consts import *
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.enumerates.token_tags import token_tags


class ImageCanvas(tk.Frame):
    """
    widget:
      - horní toolbar s labely / přepínači (viditelnost tokenů a spanů)
      - canvas_view pro zobrazení a škálování obrázku + overlaye(bounding boxy...)
      - zoom/pan (myš)
      - překreslení bounding boxů a textových štítků
      - přepočet souřadnic mezi canvas_view <=> obraz
    """

    def __init__(self, master, *, on_left_click: Optional[Callable[[tuple[int, int]], None]] = None,
        on_middle_click: Optional[Callable[[tuple[int, int]], None]] = None, on_right_click: Optional[Callable[[tuple[int, int], tuple[int, int], EventSource], None]] = None,
        root):

        super().__init__(master)
        self.root = root
        # --- Toolbar ---
        toolbar = tk.Frame(self)
        toolbar.pack(padx=(8,8), pady=(8,0))
        tk.Label(toolbar, text="Viditelnost: ").pack(side=tk.LEFT)

        self.token_enabled_value = tk.BooleanVar(value=True)
        self.span_enabled_value = tk.BooleanVar(value=True)
        self.segment_enabled_value = tk.BooleanVar(value=True)
        self.slider_value = tk.DoubleVar(value=2000)

        tk.Checkbutton(toolbar, text="Tokeny", variable=self.token_enabled_value, command=self._sync_visibility,).pack(side=tk.LEFT)
        tk.Checkbutton(toolbar, text="Spany", variable=self.span_enabled_value, command=self._sync_visibility,).pack(side=tk.LEFT, padx=(8, 0))
        tk.Checkbutton(toolbar, text="Segmenty", variable=self.segment_enabled_value, command=self._sync_visibility).pack(side=tk.LEFT, padx=(16,0))
        tk.Label(toolbar, text = "max velikost Bboxu").pack(side=tk.LEFT, padx=(24, 0))
        tk.Scale(toolbar,variable=self.slider_value, from_ = 0, to = 2000,  orient = tk.HORIZONTAL, command=self._sync_visibility,).pack(side=tk.LEFT, padx=(32, 0))

        toolbar.pack(fill=tk.X)

        # --- Canvas ---
        self.canvas = tk.Canvas(self, background="#ffffff", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=(8,8), pady=(8,8))

        # Callbacks
        self._on_left_click = on_left_click
        self._on_right_click = on_right_click
        self._on_middle_click = on_middle_click

        # Stav obrázku
        self._img_orig: Optional[Image.Image] = None
        self._img_tk: Optional[ImageTk.PhotoImage] = None

        # Optimalizace
        self._resize_after_id: Optional[str] = None

        # Pan
        self._drag_last: Optional[tuple[float, float]] = None

        # Bindy (na canvas_view)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self._on_zoom)   # Windows / macOS
        self.canvas.bind("<Button-4>", self._on_zoom)     # Linux up
        self.canvas.bind("<Button-5>", self._on_zoom)     # Linux down
        self.canvas.bind("<Button-3>", self._on_right_press)
        self.canvas.bind("<B2-Motion>", self._on_pan_move)
        self.canvas.bind("<ButtonRelease-2>", self._on_middle_release)
        self.canvas.bind("<Button-2>", self._on_middle_press)
        self.canvas.bind("<Button-1>", self._on_left_press)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        # Viditelnostní přepínače
        self.show_tokens: bool = True
        self.show_spans: bool = True
        self.show_segments: bool = True
        self.max_bbox:double = 2000.0

    # ---------- veřejné API ----------

    def display_img(self, img_path: str) -> None:
        self.canvas.delete(tk.ALL)

        if not img_path:
            return

        AppData.img_path = img_path

        self._img_orig = Image.open(img_path).convert("RGB")

        c_w = max(1, self.canvas.winfo_width())
        c_h = max(1, self.canvas.winfo_height())
        AppData.canvas_width = c_w
        AppData.canvas_height = c_h

        base_scale = min(c_w / self._img_orig.width, c_h / self._img_orig.height)
        AppData.canvas_img_scale = base_scale
        scale = base_scale * AppData.zoom

        disp = self._img_orig.resize(
            (int(self._img_orig.width * scale), int(self._img_orig.height * scale)),
            Image.BILINEAR,
        )
        self._img_tk = ImageTk.PhotoImage(disp)

        AppData.scaled_img_width = disp.width
        AppData.scaled_img_height = disp.height

        # aktuální x0, y0 jen lokálně
        x0 = (c_w - disp.width) // 2 + int(AppData.position[0])
        y0 = (c_h - disp.height) // 2 + int(AppData.position[1])

        self.canvas.create_image(x0, y0, anchor="nw", image=self._img_tk, tags=(SCAN_IMAGE,))

    def display_bounding_boxes(self) -> None:
        """Překreslí token/span/segment boxy."""
        self.canvas.delete(GROUP_BOXES)
        scale = AppData.canvas_img_scale * AppData.zoom
        x0 = (AppData.canvas_width - AppData.scaled_img_width) // 2 + int(AppData.position[0])
        y0 = (AppData.canvas_height - AppData.scaled_img_height) // 2 + int(AppData.position[1])

        if self.show_spans and AppData.invoice is not None:
            for span in AppData.invoice._spans:

                x1 = span.b_box[0] * scale + x0
                y1 = span.b_box[1] * scale + y0
                x2 = span.b_box[2] * scale + x0
                y2 = span.b_box[3] * scale + y0

                if (abs(span.b_box[0]-span.b_box[2]) > self.max_bbox or abs(span.b_box[1]-span.b_box[3]) > self.max_bbox):
                    span.visible = false
                    continue
                
                span.visible = True

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline=span.get_color_hex(),
                    tags = (GROUP_OVERLAY, GROUP_SPANS, GROUP_BOXES, SPAN_BOX_ID.format(id=span.id))
                )

        if self.show_tokens and AppData.invoice is not None:
            for token in AppData.invoice._tokens:
                x1 = token.b_box[0] * scale + x0
                y1 = token.b_box[1] * scale + y0
                x2 = token.b_box[2] * scale + x0
                y2 = token.b_box[3] * scale + y0

                if (abs(token.b_box[0]-token.b_box[2]) > self.max_bbox or abs(token.b_box[1]-token.b_box[3]) > self.max_bbox):
                    token.visible = false
                    continue

                token.visible = True

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline=token.get_color_hex(),
                    tags=(GROUP_OVERLAY, GROUP_TOKENS, GROUP_BOXES, TOKEN_BOX_ID.format(id=token.id))
                )

        if self.show_segments and AppData.invoice is not None:
            for segment in AppData.invoice._segments:
                x1 = segment.b_box[0] * scale + x0
                y1 = segment.b_box[1] * scale + y0
                x2 = segment.b_box[2] * scale + x0
                y2 = segment.b_box[3] * scale + y0

                if (abs(segment.b_box[0]-segment.b_box[2]) > self.max_bbox or abs(segment.b_box[1]-segment.b_box[3]) > self.max_bbox):
                    segment.visible = false
                    continue

                segment.visible = True

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline=segment.get_color_hex(),
                    tags=(GROUP_OVERLAY, GROUP_SEGMENTS, GROUP_BOXES, SEGMENT_BOX_ID.format(id=segment.id))
                )


    def display_text(self) -> None:
        """Překreslí textové štítky nad boxy."""
        self.canvas.delete("text")
        scale = AppData.canvas_img_scale * AppData.zoom
        x0 = (AppData.canvas_width - AppData.scaled_img_width) // 2 + int(AppData.position[0])
        y0 = (AppData.canvas_height - AppData.scaled_img_height) // 2 + int(AppData.position[1])

        if self.show_spans and AppData.invoice is not None:
            for span in AppData.invoice._spans:
                if not span.visible:
                    continue
                x1 = span.b_box[0] * scale + x0
                y1 = span.b_box[1] * scale + y0
                if span.tag != span_tags.O:
                    self.canvas.create_text(
                        x1, y1 - 5,
                        fill="blue",
                        text=span.tag.name,
                        font="Times 8",
                        tags = (GROUP_OVERLAY, GROUP_SPAN_TEXT, GROUP_TEXT, SPAN_TEXT_ID.format(id=span.id))
                    )

        if self.show_tokens and AppData.invoice is not None:
            for token in AppData.invoice._tokens:
                if(not token.visible):
                    continue
                x1 = token.b_box[0] * scale + x0
                y1 = token.b_box[1] * scale + y0
                if token.tag != token_tags.O:
                    self.canvas.create_text(
                        x1, y1 - 5,
                        fill="blue",
                        text=token.tag.name,
                        font="Times 8",
                        tags=(GROUP_OVERLAY, GROUP_TOKEN_TEXT, GROUP_TEXT, TOKEN_TEXT_ID.format(id=token.id))
                    )

        if self.show_segments and AppData.invoice is not None:
            for segment in AppData.invoice._segments:
                if(not segment.visible):
                    continue
                x1 = segment.b_box[0] * scale + x0
                y1 = segment.b_box[1] * scale + y0
                if segment.tag != segment_tags.O:
                    self.canvas.create_text(
                        x1, y1 - 5,
                        fill="blue",
                        text=segment.tag.name,
                        font="Times 8",
                        tags=(GROUP_OVERLAY, GROUP_SEGMENT_TEXT, GROUP_TEXT, SEGMENT_TEXT_ID.format(id=segment.id))
                    )


    def full_redraw(self) -> None:
        """Překreslí obrázek i overlaye."""
        if AppData.img_path:
            self.display_img(AppData.img_path)
            self.display_bounding_boxes() #musí být před display_text
            self.display_text()

    def partial_redraw(self) -> None:
        self.display_bounding_boxes() #musí být před display_text
        self.display_text()

    def sync_bounding_boxes_color(self) -> bool:
        for tok in AppData.invoice._tokens:
            self.canvas.itemconfig(TOKEN_BOX_ID.format(id=tok.id), outline=tok.get_color_hex())
        
        for span in AppData.invoice._spans:
            self.canvas.itemconfig(SPAN_BOX_ID.format(id=span.id), outline=span.get_color_hex())

        for segment in AppData.invoice._segments:
            self.canvas.itemconfig(SEGMENT_BOX_ID.format(id=segment.id), outline=segment.get_color_hex())
        
        return True

    # ---------- vnitřní obsluha událostí ----------

    def _on_canvas_resize(self, _ev) -> None:
        if self._img_orig is None or not AppData.img_path:
            return
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(120, self.full_redraw)

    def _on_zoom(self, event) -> None:
        delta = getattr(event, "delta", 0)
        num = getattr(event, "num", None)
        if delta > 0 or num == 4:
            zoom_coef = 1.1
        elif delta < 0 or num == 5:
            zoom_coef = 0.9
        else:
            return
        AppData.zoom *= zoom_coef
        self.full_redraw()

    def _on_right_press(self, event) -> None:
        if self._on_right_click:
            self._on_right_click(
                (event.x_root, event.y_root),
                (event.x, event.y),
                EventSource.IMAGE_CANVAS
            )

    def _on_pan_move(self, event) -> None:
        if self._drag_last is None:
            self._on_middle_press(event)
            return
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        dx, dy = x - self._drag_last[0], y - self._drag_last[1]
        self._drag_last = (x, y)

        self.canvas.move(SCAN_IMAGE, dx, dy)
        self.canvas.move(GROUP_OVERLAY, dx, dy)

        AppData.position = (AppData.position[0] + dx, AppData.position[1] + dy)
        AppData.x0 = AppData.x0 + dx
        AppData.y0 = AppData.y0 + dy  

    def _on_middle_release(self, _ev) -> None:
        self._drag_last = None

    def _on_left_press(self, event) -> None:
        if AppData.last_mouse_click_position is not None and AppData.context_menu_clicked_option == ContextMenuOptions.CREATE_TOKEN:
            self.root.create_token((event.x, event.y))
        elif AppData.last_mouse_click_position is not None and AppData.context_menu_clicked_option == ContextMenuOptions.CREATE_SEGMENT:
            self.root.create_segment((event.x, event.y))
        
        if self._on_left_click:
            self._on_left_click((event.x, event.y))
        
        

    def _on_mouse_move(self, event) -> None:
        event.x, event.y
        self.canvas.delete("move_rectangle")

        if AppData.last_mouse_click_position != None:
            self.canvas.create_rectangle(AppData.last_mouse_click_position[0],
                                        AppData.last_mouse_click_position[1],
                                        event.x,
                                        event.y,
                                        tags="move_rectangle")
        ...

    def _on_middle_press(self, event) -> None:
        self._drag_last = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if self._on_middle_click:
            self._on_middle_click((event.x, event.y))

    def _canvas_to_image(self, x_canvas: int, y_canvas: int) -> tuple[float, float]:
        """Převede souřadnice v canvasu na souřadnice v obrázku."""
        scale = AppData.canvas_img_scale * AppData.zoom
        x0 = (AppData.canvas_width - AppData.scaled_img_width) // 2 + int(AppData.position[0])
        y0 = (AppData.canvas_height - AppData.scaled_img_height) // 2 + int(AppData.position[1])
        return (x_canvas - x0) / scale, (y_canvas - y0) / scale

    def _sync_visibility(self, *kwargs) -> None:
        """Reakce na přepínače viditelnosti v toolbaru."""
        self.show_tokens = bool(self.token_enabled_value.get())
        self.show_spans = bool(self.span_enabled_value.get())
        self.show_segments = bool(self.segment_enabled_value.get())

        self.max_bbox = double(self.slider_value.get())

        self.partial_redraw()
