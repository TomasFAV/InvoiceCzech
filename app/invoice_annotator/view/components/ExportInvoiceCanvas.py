from dataclasses import dataclass, field
import tkinter as tk
from typing import Callable

from invoice_annotator.view.View import View
from invoice_annotator.view.interfaces.IDataAnnotator import IMainWindow
from invoice_annotator.view.components.Component import Component
from invoice_annotator.utils.consts import TOKEN_TAG, TOKEN_TEXT_TAG
from invoice_annotator.view.components.BoundingBoxLayer import DrawBoxConfig, DrawBoxLayer, Drawable
from invoice_annotator.view.components.Canvas import ImageCanvas
    
@dataclass
class ExportInvoiceToolBar:
    tokens: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    slider: tk.DoubleVar = field(default_factory=lambda: tk.DoubleVar(value=2000.0))

@dataclass
class ExportInvoiceData:
    tokens: list[Drawable] = field(default_factory=list)

@dataclass
class ExportInvoiceCanvasConfig:
    ...

class ExportInvoiceCanvas(Component):

    def __init__(self, master, window:IMainWindow, parent_view:View, config:ExportInvoiceCanvasConfig|None = None):
        super().__init__(window, parent_view, master)

        self.config:ExportInvoiceCanvasConfig|None = config
        self.toolbar: ExportInvoiceToolBar = ExportInvoiceToolBar()
        self.data:ExportInvoiceData = ExportInvoiceData()

        self.canvas:ImageCanvas|None = None
        self.tokenLayer:DrawBoxLayer|None = None


        self.build()

    def build(self):
        self.build_toolbar()
        self.build_canvas()
        self.build_layers()
    
    def build_toolbar(self):
        toolbar = tk.Frame(self)
        toolbar.pack(fill=tk.X, padx=8, pady=(8, 0))

        tk.Label(toolbar, text="Viditelnost:").pack(side=tk.LEFT)

        tk.Checkbutton(toolbar, text="Tokeny", variable=self.toolbar.tokens, command=self.partial_redraw).pack(side=tk.LEFT)

        tk.Label(toolbar, text="max velikost BBoxu").pack(side=tk.LEFT, padx=(24, 0))

        tk.Scale(toolbar, variable=self.toolbar.slider, from_=0, to=2000, orient=tk.HORIZONTAL, command=self.partial_redraw,).pack(side=tk.LEFT, padx=(32, 0))

    def build_canvas(self):
        self.canvas = ImageCanvas(self)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def build_layers(self):
        self.tokenLayer = DrawBoxLayer(self.canvas, DrawBoxConfig(TOKEN_TAG, TOKEN_TEXT_TAG))


    def full_redraw(self, *args, **kwargs) -> None:
        self.toogle_tokens()

        self.canvas.full_redraw()
        self.tokenLayer.full_redraw()
    
    def partial_redraw(self, *args, **kwargs) -> None:
        self.toogle_tokens()

        self.canvas.partial_redraw()
        self.tokenLayer.partial_redraw()

    def load(self, img_path:str="", tokens: list[Drawable]|None = None,):
        self.load_image(img_path)
        self.load_tokens(tokens)

    def load_image(self, img_path:str) -> None:
        self.canvas.load_image(img_path)
    
    def load_tokens(self, tokens: list[Drawable]) ->None:
        if not tokens:
            return 
        
        self.data.tokens = tokens
        self.tokenLayer.load_objects(tokens)


    def canvas_to_image(self, coordinates: tuple[float, float])->tuple[float, float]:
        self.canvas.canvas_to_image(coordinates[0], coordinates[1])

    def toogle_tokens(self, *args) -> None:
        if(self.toolbar.tokens.get()):
           self.tokenLayer.hide_objects(self.toolbar.slider.get())
        else:
            self.tokenLayer.hide_objects()

    def slide(self, *args) -> None:
        self.tokenLayer.hide_objects(self.toolbar.slider.get())