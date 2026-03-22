from __future__ import annotations
from json import tool
import tkinter as tk
from typing import Callable, Optional
from PIL import Image, ImageTk
from click import command
from httpx import delete
from networkx import draw
from numpy import double, isin
import scipy as sp
from sympy import false, true

from invoice_annotator.utils.GSegment import GSegment
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
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
        root=None, on_create_token=None):

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

        #proměnné související s zoomem, pohybem obrázku canvasu
        self.img_path: None|str = None
        self.base_img_scale:float = 1.0
        self.image_zoom: float = 1.0
        self.scaled_img_width:None|float = None
        self.scaled_img_height:None|float = None

        self.image_position: tuple[float, float] = (0,0)

        self.last_mouse_click_position:tuple[float, float]|None = None
        self.context_menu_clicked_option:ContextMenuOptions = ContextMenuOptions.OTHER

        #####
        self._create_start_canvas: tuple[int, int] | None = None
        self._current_mouse_canvas: tuple[int, int] | None = None
        self._on_create_token = on_create_token

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

    def display_img(self, img_path: None|str) -> None:
        self.canvas.delete(tk.ALL)

        if not img_path:
            return

        self.img_path = img_path

        self._img_orig = Image.open(img_path).convert("RGB")

        c_w = max(1, self.canvas.winfo_width())
        c_h = max(1, self.canvas.winfo_height())
        AppData.canvas_width = c_w
        AppData.canvas_height = c_h

        base_scale = min(c_w / self._img_orig.width, c_h / self._img_orig.height)
        self.base_img_scale = base_scale
        scale = base_scale * self.image_zoom

        disp = self._img_orig.resize(
            (int(self._img_orig.width * scale), int(self._img_orig.height * scale)),
            Image.BILINEAR,
        )
        self._img_tk = ImageTk.PhotoImage(disp)

        self.scaled_img_width = disp.width
        self.scaled_img_height = disp.height

        # aktuální x0, y0 jen lokálně
        x0 = (c_w - disp.width) // 2 + int(self.image_position[0])
        y0 = (c_h - disp.height) // 2 + int(self.image_position[1])

        self.canvas.create_image(x0, y0, anchor="nw", image=self._img_tk, tags=(SCAN_IMAGE,))

    def display_bounding_box(self, drawable:GSpan|GToken|GSegment):
        
        if(not isinstance(drawable, GSpan) and not isinstance(drawable, GToken) and not isinstance(drawable, GSegment)):
            return

        scale = self.base_img_scale * self.image_zoom
        x0 = (self.canvas.winfo_width() - self.scaled_img_width) // 2 + int(self.image_position[0])
        y0 = (self.canvas.winfo_height() - self.scaled_img_height) // 2 + int(self.image_position[1])

        x1 = drawable.b_box[0] * scale + x0
        y1 = drawable.b_box[1] * scale + y0
        x2 = drawable.b_box[2] * scale + x0
        y2 = drawable.b_box[3] * scale + y0
        
        if (abs(drawable.b_box[0]-drawable.b_box[2]) > self.max_bbox or abs(drawable.b_box[1]-drawable.b_box[3]) > self.max_bbox):
            drawable.visible = false
            return
        
        drawable.visible = True

        box_tags = ()
        text_tags = ()
        if isinstance(drawable, GSpan):
            box_tags = (GROUP_OVERLAY, GROUP_SPANS, GROUP_BOXES, SPAN_BOX_ID.format(id=drawable.id))
            text_tags = (GROUP_OVERLAY, GROUP_SPAN_TEXT, GROUP_TEXT, SPAN_TEXT_ID.format(id=drawable.id))
        elif isinstance(drawable, GToken):
            box_tags = (GROUP_OVERLAY, GROUP_TOKENS, GROUP_BOXES, TOKEN_BOX_ID.format(id=drawable.id))
            text_tags = (GROUP_OVERLAY, GROUP_TOKEN_TEXT, GROUP_TEXT, TOKEN_TEXT_ID.format(id=drawable.id))
        elif isinstance(drawable, GSegment):
            box_tags = tags=(GROUP_OVERLAY, GROUP_SEGMENTS, GROUP_BOXES, SEGMENT_BOX_ID.format(id=drawable.id))
            text_tags = (GROUP_OVERLAY, GROUP_SEGMENT_TEXT, GROUP_TEXT, SEGMENT_TEXT_ID.format(id=drawable.id))
        else:
            return
        
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=drawable.get_color_hex(), tags = box_tags)
        
        #nevykreslujeme O tag
        if drawable.tag.code != 0:  
            self.canvas.create_text(x1, y1 - 5, fill="blue", text=drawable.tag.name, font="Times 8", tags=text_tags)

    def display_bounding_boxes(self) -> None:
        """Překreslí token/span/segment boxy."""
        self.canvas.delete(GROUP_BOXES)
        self.canvas.delete("text")

        if self.show_spans and AppData.invoice is not None:
            for span in AppData.invoice._spans:
                self.display_bounding_box(span)

        if self.show_tokens and AppData.invoice is not None:
            for token in AppData.invoice._tokens:
                self.display_bounding_box(token)

        if self.show_segments and AppData.invoice is not None:
            for segment in AppData.invoice._segments:
                self.display_bounding_box(segment)


    def full_redraw(self) -> None:
        """Překreslí obrázek i overlaye."""
        if self.img_path:
            self.display_img(self.img_path)
            self.display_bounding_boxes() #musí být před display_text

    def partial_redraw(self) -> None:
        self.display_bounding_boxes() #musí být před display_text

    def sync_bounding_boxes_color(self) -> bool:
        for tok in AppData.invoice._tokens:
            self.canvas.itemconfig(TOKEN_BOX_ID.format(id=tok.id), outline=tok.get_color_hex())
        
        for span in AppData.invoice._spans:
            self.canvas.itemconfig(SPAN_BOX_ID.format(id=span.id), outline=span.get_color_hex())

        for segment in AppData.invoice._segments:
            self.canvas.itemconfig(SEGMENT_BOX_ID.format(id=segment.id), outline=segment.get_color_hex())
        
        return True

    def begin_create_box(self, start_pos_canvas: tuple[int, int]) -> None:
        self._create_start_canvas = start_pos_canvas

    def finish_create_box(self, end_pos_canvas: tuple[int, int]) -> tuple[float, float, float, float] | None:
        if self._create_start_canvas is None:
            return None

        x1, y1 = self._canvas_to_image(*self._create_start_canvas)
        x2, y2 = self._canvas_to_image(*end_pos_canvas)

        self._create_start_canvas = None
        self.canvas.delete("move_rectangle")

        return (
            min(x1, x2),
            min(y1, y2),
            max(x1, x2),
            max(y1, y2),
    )

    # ---------- vnitřní obsluha událostí ----------

    def _on_canvas_resize(self, _ev) -> None:
        if self._img_orig is None or not self.img_path:
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
        self.image_zoom *= zoom_coef
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

        self.image_position = (self.image_position[0] + dx, self.image_position[1] + dy)


    def _on_middle_release(self, _ev) -> None:
        self._drag_last = None

    def _on_left_press(self, event) -> None:
        if self._create_start_canvas is not None and self.context_menu_clicked_option == ContextMenuOptions.CREATE_TOKEN:
            self.root.create_token((event.x, event.y))
        elif self._create_start_canvas is not None and self.context_menu_clicked_option == ContextMenuOptions.CREATE_SEGMENT:
            self.root.create_segment((event.x, event.y))
        
        if self._on_left_click:
            self._on_left_click((event.x, event.y))
        
        

    def _on_mouse_move(self, event) -> None:
        self._current_mouse_canvas = (event.x, event.y) #uložim aktualni pozici myši
        self.canvas.delete("move_rectangle")

        if self._create_start_canvas is not None:
            self.canvas.create_rectangle(self._create_start_canvas[0],
                                        self._create_start_canvas[1],
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
        scale = self.base_img_scale * self.image_zoom
        x0 = (self.canvas.winfo_width() - self.scaled_img_width) // 2 + int(self.image_position[0])
        y0 = (self.canvas.winfo_height() - self.scaled_img_height) // 2 + int(self.image_position[1])
        return (x_canvas - x0) / scale, (y_canvas - y0) / scale

    def _sync_visibility(self, *kwargs) -> None:
        """Reakce na přepínače viditelnosti v toolbaru."""
        self.show_tokens = bool(self.token_enabled_value.get())
        self.show_spans = bool(self.span_enabled_value.get())
        self.show_segments = bool(self.segment_enabled_value.get())

        self.max_bbox = double(self.slider_value.get())

        self.partial_redraw()
