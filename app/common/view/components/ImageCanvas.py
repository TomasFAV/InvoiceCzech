from dataclasses import dataclass, field
import tkinter as tk
from PIL import Image, ImageTk
from common.utils.consts import GROUP_OVERLAY, SCAN_IMAGE

@dataclass
class ToolBar:
    tokens: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    spans: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    segments: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    slider: tk.DoubleVar = field(default_factory=lambda: tk.DoubleVar(value=2000.0))

@dataclass
class ImageObject:
    path:str = ""
    zoom: float = 1.0
    padding:tuple[float, float] = (0,0)
    _drag_last:tuple[float, float] | None = None

    original_image: Image.Image | None = None
    tk_image: ImageTk.PhotoImage | None = None



class ImageCanvas(tk.Canvas):

    def __init__(self, master):
        super().__init__(master, background="#ffffff", highlightthickness=0)

        self._resize_after_id:str = ""
        self.image = ImageObject() 
        self._bind_events()

    def _bind_events(self) -> None:
        self.bind("<Configure>", self._on_canvas_resize, add="+")
        self.bind("<MouseWheel>", self._on_zoom, add="+")
        self.bind("<Button-4>", self._on_zoom, add="+")
        self.bind("<Button-5>", self._on_zoom, add="+")
        
        self.bind("<Button-2>", self._on_middle_press, add="+")
        self.bind("<ButtonRelease-2>", self._on_middle_release, add="+")
        self.bind("<B2-Motion>", self._on_pan_move, add="+")

    def image_scale(self) -> float:
        if self.image.original_image is None:
            return 1.0

        canvas_width = max(1, self.winfo_width())
        canvas_height = max(1, self.winfo_height())

        img_width = self.image.original_image.width
        img_height = self.image.original_image.height

        base_scale = min(canvas_width / img_width, canvas_height / img_height)
        
        return base_scale * self.image.zoom

    def load_image(self, img_path: str | None) -> None:
        self.delete(tk.ALL)

        if not img_path:
            self.image = ImageObject()
            return

        self.image.path = img_path
        self.image.zoom = 1.0
        self.image.padding = (0.0, 0.0)
        self.image.original_image = Image.open(img_path).convert("RGB")

        self.redraw_image()

    def redraw_image(self) -> None:
        self.delete(SCAN_IMAGE)

        if self.image.original_image is None:
            return

        scale = self.image_scale()
        orig = self.image.original_image

        new_width = max(1, int(orig.width * scale))
        new_height = max(1, int(orig.height * scale))

        resized_image = orig.resize((new_width, new_height), Image.BILINEAR)
        self.image.tk_image = ImageTk.PhotoImage(resized_image)

        x0 = (self.winfo_width() - new_width) // 2 + int(self.image.padding[0])
        y0 = (self.winfo_height() - new_height) // 2 + int(self.image.padding[1])

        self.create_image(x0,y0,anchor="nw",image=self.image.tk_image,tags=(SCAN_IMAGE,),)


    def full_redraw(self) -> None:
        if self.image.path:
            self.redraw_image()
    
    def partial_redraw(self) -> None:
        ...
        #self.full_redraw()
        
    def _on_canvas_resize(self, _event) -> None:
        if self.image.original_image is None or not self.image.path:
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

        self.image.zoom *= zoom_coef
        self.full_redraw()

    def _on_middle_press(self, event) -> None:
        self.image._drag_last = (self.canvasx(event.x), self.canvasy(event.y),)

    def _on_middle_release(self, _event) -> None:
        self.image._drag_last = None
    
    def _on_pan_move(self, event) -> None:
        if self.image._drag_last is None:
            self._on_middle_press(event)
            return

        x = self.canvasx(event.x)
        y = self.canvasy(event.y)
        dx = x - self.image._drag_last[0]
        dy = y - self.image._drag_last[1]
        self.image._drag_last = (x, y)

        self.move(SCAN_IMAGE, dx, dy)
        self.move(GROUP_OVERLAY, dx, dy)
        self.image.padding = (self.image.padding[0] + dx, self.image.padding[1] + dy)


    #pro převod souřadnic
    def canvas_to_image(self, x_canvas: int, y_canvas: int) -> tuple[int, int]:
        scale = self.image_scale()

        if not scale or self.image.original_image is None:
            return 0.0, 0.0

        x0 = (self.winfo_width() - self.image.tk_image.width()) // 2 + int(self.image.padding[0])
        y0 = (self.winfo_height() - self.image.tk_image.height()) // 2 + int(self.image.padding[1])

        return (int)((x_canvas - x0) / scale), (int)((y_canvas - y0) / scale)
