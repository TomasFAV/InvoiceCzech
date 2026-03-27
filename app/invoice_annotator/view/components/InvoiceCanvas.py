from dataclasses import dataclass, field
import tkinter as tk
from typing import Callable

from shared.OperationResult import OperationResult
from invoice_annotator.view.components.Menu import Menu
from invoice_annotator.view.View import View
from invoice_annotator.view.interfaces.IDataAnnotator import IMainWindow
from invoice_annotator.view.components.Component import Component
from invoice_annotator.utils.consts import CREATE_SEGMENT, CREATE_TAG, CREATE_TOKEN, REMOVE, RESET, SEGMENT_TAG, SEGMENT_TEXT_TAG, SPAN_TAG, SPAN_TEXT_TAG, TOKEN_TAG, TOKEN_TEXT_TAG
from invoice_annotator.view.components.BoundingBoxLayer import DrawBoxConfig, DrawBoxLayer, Drawable
from invoice_annotator.view.components.Canvas import ImageCanvas
    
@dataclass
class ToolBar:
    tokens: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    spans: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    segments: tk.BooleanVar = field(default_factory=lambda: tk.BooleanVar(value=True))
    slider: tk.DoubleVar = field(default_factory=lambda: tk.DoubleVar(value=2000.0))

@dataclass
class Data:
    tokens: list[Drawable] = field(default_factory=list)
    spans: list[Drawable] = field(default_factory=list)
    segments: list[Drawable] = field(default_factory=list)

@dataclass
class InvoiceCanvasConfig:
    leftClickHandlerObjectCollision:Callable|None = None #volá se když se klikne na nějaký objekt v overlayích
    leftClickHandlerNoObjectCollision:Callable|None = None #volá se když se klikne pouze na plátno
    rightClickHandler:Callable|None = None
    contextMenuHandler:Callable|None = None

class InvoiceCanvas(Component):

    def __init__(self, master, window:IMainWindow, parent_view:View, config:InvoiceCanvasConfig|None = None):
        super().__init__(window, parent_view, master)

        self.config:InvoiceCanvasConfig|None = config
        self.toolbar: ToolBar = ToolBar()
        self.data:Data = Data()

        self.canvas:ImageCanvas|None = None

        self.tokenLayer:DrawBoxLayer|None = None
        self.spanLayer:DrawBoxLayer|None = None
        self.segmentLayer:DrawBoxLayer|None = None

        self.context_menu: Menu|None = None

        self.build()

    def build(self):
        self.build_toolbar()
        self.build_canvas()
        self.build_layers()
        self.build_context_menu()
    
    def build_toolbar(self):
        toolbar = tk.Frame(self)
        toolbar.pack(fill=tk.X, padx=8, pady=(8, 0))

        tk.Label(toolbar, text="Viditelnost:").pack(side=tk.LEFT)

        tk.Checkbutton(toolbar, text="Tokeny", variable=self.toolbar.tokens, command=self.partial_redraw).pack(side=tk.LEFT)

        tk.Checkbutton(toolbar, text="Spany", variable=self.toolbar.spans, command=self.partial_redraw).pack(side=tk.LEFT, padx=(8, 0))

        tk.Checkbutton(toolbar, text="Segmenty", variable=self.toolbar.segments,command=self.partial_redraw).pack(side=tk.LEFT, padx=(16, 0))

        tk.Label(toolbar, text="max velikost BBoxu").pack(side=tk.LEFT, padx=(24, 0))

        tk.Scale(toolbar, variable=self.toolbar.slider, from_=0, to=2000, orient=tk.HORIZONTAL, command=self.partial_redraw,).pack(side=tk.LEFT, padx=(32, 0))

    def build_canvas(self):
        self.canvas = ImageCanvas(self)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    def build_layers(self):
        self.tokenLayer = DrawBoxLayer(self.canvas, DrawBoxConfig(TOKEN_TAG, TOKEN_TEXT_TAG, self.left_click_handler_object_collision,
                                                                 self.left_click_handler_no_object_collision, self.right_click_handler, True))
        self.spanLayer = DrawBoxLayer(self.canvas, DrawBoxConfig(SPAN_TAG, SPAN_TEXT_TAG, self.left_click_handler_object_collision,
                                                                 self.left_click_handler_no_object_collision, self.right_click_handler))
        self.segmentLayer = DrawBoxLayer(self.canvas, DrawBoxConfig(SEGMENT_TAG, SEGMENT_TEXT_TAG, self.left_click_handler_object_collision,
                                                                    self.left_click_handler_no_object_collision, self.right_click_handler))

    def build_context_menu(self):
        self.context_menu = Menu(self.canvas,
            {
                TOKEN_TAG:[
                    ("Resetovat tag tokenu", RESET, self.config.contextMenuHandler),  
                    ("Odstranit token", REMOVE,  self.config.contextMenuHandler)
                ],
                SPAN_TAG:[
                    ("Odstranit Span", REMOVE, self.config.contextMenuHandler)
                ],
                SEGMENT_TAG:[
                    ("Odstranit Segment", REMOVE, self.config.contextMenuHandler),
                ],
                #když jsem neklikl na objekt
                None: [
                    ("Vytvořit Token", CREATE_TOKEN, self.config.contextMenuHandler),
                    ("Vytvořit Segment", CREATE_SEGMENT, self.config.contextMenuHandler)
                ]
            }
        )

    #------------------------------EVENT HANDLERY----------------------------

    def left_click_handler_object_collision(self, *args, **kwargs):
        self.config.leftClickHandlerObjectCollision(*args, **kwargs)
        self.context_menu.hide()

    def left_click_handler_no_object_collision(self, *args, **kwargs):
        self.config.leftClickHandlerNoObjectCollision(*args, **kwargs)
        self.context_menu.hide()

    def right_click_handler(self, tag:str|None, id:int|None, **kwargs) -> None:
        self.context_menu.show(tag, position=kwargs.get("mouse_click_window_position"), id=id, mouse_click_canvas_position=kwargs.get("mouse_click_canvas_position"))

    #------------------------------EVENT HANDLERY----------------------------
    #----------------------------------KONEC----------------------------

    def begin_token_box_creation(self, start_position_canvas:tuple[int, int])->None:
        self.tokenLayer.begin_box(start_position_canvas)

    def begin_segment_box_creation(self, start_position_canvas:tuple[int, int])->None:
        self.segmentLayer.begin_box(start_position_canvas)

    def end_token_box_creation(self, start_position_canvas: tuple[int, int])->OperationResult:
        return OperationResult(True, self.tokenLayer.end_box(start_position_canvas))
    
    def end_segment_box_creation(self, start_position_canvas: tuple[int, int])->OperationResult:
        return OperationResult(True, self.segmentLayer.end_box(start_position_canvas))


    def full_redraw_layers(self):
        self.toogle_layers()

        self.tokenLayer.full_redraw()
        self.spanLayer.full_redraw()
        self.segmentLayer.full_redraw()

    def partial_redraw_layers(self, *args, **kwargs):
        self.toogle_layers()

        self.tokenLayer.partial_redraw()
        self.spanLayer.partial_redraw()
        self.segmentLayer.partial_redraw()

    def full_redraw(self, *args, **kwargs) -> None:
        self.canvas.full_redraw()
        self.full_redraw_layers()
    
    def partial_redraw(self) -> None:
        self.canvas.partial_redraw()
        self.partial_redraw_layers()

    def load(self, img_path:str="", tokens: list[Drawable]|None = None, spans: list[Drawable]|None = None, segments: list[Drawable]|None = None):
        self.load_image(img_path)

        self.load_tokens(tokens)
        self.load_spans(spans)
        self.load_segments(segments)

    def load_image(self, img_path:str) -> None:
        self.canvas.load_image(img_path)
    
    def load_tokens(self, tokens: list[Drawable]) ->None:
        if not tokens:
            return 
        
        self.data.tokens = tokens
        self.tokenLayer.load_objects(tokens)

    def load_spans(self, spans: list[Drawable]) ->None:
        if not spans:
            return 
        
        self.data.spans = spans
        self.spanLayer.load_objects(spans)


    def load_segments(self, segments: list[Drawable]) ->None:
        if not segments:
            return 
        
        self.data.segments = segments
        self.segmentLayer.load_objects(segments)


    def canvas_to_image(self, coordinates: tuple[float, float])->tuple[float, float]:
        self.canvas.canvas_to_image(coordinates[0], coordinates[1])

    def toogle_layers(self)->None:
        self.toogle_tokens()
        self.toogle_spans()
        self.toogle_segments()

    def toogle_tokens(self, *args) -> None:
        if(self.toolbar.tokens.get()):
           self.tokenLayer.hide_objects(self.toolbar.slider.get())
        else:
            self.tokenLayer.hide_objects()

    def toogle_spans(self, *args) -> None:
        if(self.toolbar.spans.get()):
           self.spanLayer.hide_objects(self.toolbar.slider.get())
        else:
            self.spanLayer.hide_objects()

    def toogle_segments(self, *args) -> None:
        if(self.toolbar.segments.get()):
           self.segmentLayer.hide_objects(self.toolbar.slider.get())
        else:
            self.segmentLayer.hide_objects()

    def slide(self, *args) -> None:
        self.tokenLayer.hide_objects(self.toolbar.slider.get())
        self.spanLayer.hide_objects(self.toolbar.slider.get())
        self.segmentLayer.hide_objects(self.toolbar.slider.get())
