from dataclasses import dataclass
from typing import Callable
from common.utils.consts import GROUP_OVERLAY
from common.invoice.models.GSegment import GSegment
from common.invoice.models.GToken import GToken
from common.invoice.models.GSpan import GSpan
from common.view.components.ImageCanvas import ImageCanvas

Drawable = GSpan | GToken | GSegment

@dataclass
class DrawBoxConfig:
    boxTag:str = ""
    textTag:str = ""
    leftClickHandlerObjectCollision: Callable| None = None
    leftClickHandlerNoObjectCollision: Callable| None = None
    rightClickHandler: Callable| None = None
    triggerRightClickEvenWithoutCollision: bool = False



class DrawBoxLayer:

    """Layer starající se o logiku a vykreslování bounding boxů na libovolný ImageCanvas"""    

    def __init__(self, canvas:ImageCanvas, config:DrawBoxConfig):
        self.canvas:ImageCanvas = canvas
        self.config:DrawBoxConfig = config

        self._resize_after_id:str = ""
        self.data:list[Drawable] = list()

        self._box_start_position:tuple[int, int]|None = None


        self.build()
        self._bind_events()

    def _bind_events(self) -> None:
        self.canvas.bind("<Motion>", self._on_mouse_move, add="+")
        self.canvas.bind("<Button-3>", self._on_right_press, add="+")
        self.canvas.bind("<Button-1>", self._on_left_press, add="+")
        
        self.canvas.bind("<Configure>", self._on_canvas_resize, add="+")
        self.canvas.bind("<MouseWheel>",  self.full_redraw, add="+")
        self.canvas.bind("<Button-4>",  self.full_redraw, add="+")
        self.canvas.bind("<Button-5>",  self.full_redraw, add="+")
    

    def build(self) -> None:
        pass

    def partial_redraw(self, *args, **kwargs) -> None:
        self.display_objects()

    def full_redraw(self, *args, **kwargs) -> None:
        self.display_objects()

    def hide_objects(self, max_size:float = 0) -> None:
        for obj in self.data:
            width = abs(obj.b_box[0] - obj.b_box[2])
            height = abs(obj.b_box[1] - obj.b_box[3])

            if width > max_size or height > max_size:
                obj.visible = False
            else:
                obj.visible = True
        self.full_redraw()

    def show_all_objects(self)->None:
        for obj in self.data:
            obj.visible = True
        self.full_redraw()

    def clear_objects(self) -> None:
        self.canvas.delete(self.config.boxTag)
        self.canvas.delete(self.config.textTag)

    def load_objects(self, objects:list[Drawable])->None:
        self.data = objects
        self.display_objects()

    def display_objects(self) -> None:
        self.canvas.delete(self.config.boxTag)
        self.canvas.delete(self.config.textTag)

        for item in self.data:
            self.__display_object(item)

    def __display_object(self, drawable: Drawable) -> None:
        if self.canvas.image.tk_image is None or not drawable.visible:
            return

        scale = self.canvas.image_scale()
        canvas_x0 = (self.canvas.winfo_width() - self.canvas.image.tk_image.width()) // 2 + int(self.canvas.image.padding[0])
        canvas_y0 = (self.canvas.winfo_height() - self.canvas.image.tk_image.height()) // 2 + int(self.canvas.image.padding[1])

        x1 = drawable.b_box[0] * scale + canvas_x0
        y1 = drawable.b_box[1] * scale + canvas_y0
        x2 = drawable.b_box[2] * scale + canvas_x0
        y2 = drawable.b_box[3] * scale + canvas_y0

        self.canvas.create_rectangle(x1,y1, x2,y2, outline=drawable.get_color_hex(),
            tags=(self.config.boxTag, self.config.boxTag+str(drawable.id),GROUP_OVERLAY),
        )

        if drawable.tag.code != 0:
            self.canvas.create_text(x1, y1 - 5, fill="blue", text=drawable.tag.name,
                font="Times 8", tags=(self.config.textTag, self.config.textTag+str(drawable.id), GROUP_OVERLAY))

    #je potřeba odložit o chvíli redraw po změně velikosti okna
    def _on_canvas_resize(self, _event) -> None:
        if self._resize_after_id:
            self.canvas.after_cancel(self._resize_after_id)

        self._resize_after_id = self.canvas.after(120, self.full_redraw)

    def _on_left_press(self, event) -> None:
        leftClickHandlerObjectCollision:Callable|None = self.config.leftClickHandlerObjectCollision
        leftClickHandlerNoObjectCollision:Callable|None = self.config.leftClickHandlerNoObjectCollision
        if not leftClickHandlerObjectCollision:
            return

        mouse_click_position = self.canvas.canvas_to_image(event.x, event.y)
        

        for item in self.data:
            if (item.visible and
                
                mouse_click_position[0] > item.b_box[0] and mouse_click_position[0] < item.b_box[2] and 
                mouse_click_position[1] > item.b_box[1] and mouse_click_position[1] < item.b_box[3]):
                
                leftClickHandlerObjectCollision(tag=self.config.boxTag, id=item.id, 
                                 mouse_click_canvas_position=(event.x, event.y),
                                 mouse_click_window_position=(event.x_root, event.y_root))
                return
        
        if leftClickHandlerNoObjectCollision:
            leftClickHandlerNoObjectCollision(mouse_click_canvas_position=(event.x, event.y), mouse_click_window_position=(event.x_root, event.y_root))        


    def _on_right_press(self, event) -> None:
        rightClickHandler:Callable|None = self.config.rightClickHandler
        if not rightClickHandler:
            return

        mouse_click_position = self.canvas.canvas_to_image((int)(event.x), (int)(event.y))

        for item in self.data:
            if (mouse_click_position[0] > item.b_box[0] and mouse_click_position[0] < item.b_box[2] and 
                mouse_click_position[1] > item.b_box[1] and mouse_click_position[1] < item.b_box[3] and item.visible):
                rightClickHandler(tag=self.config.boxTag, id=item.id, 
                                  mouse_click_canvas_position=(event.x, event.y),
                                  mouse_click_window_position=(event.x_root, event.y_root))
                return
            
        if self.config.triggerRightClickEvenWithoutCollision:
            rightClickHandler(tag=None, id=None, mouse_click_canvas_position=(event.x, event.y), mouse_click_window_position=(event.x_root, event.y_root))

    def begin_box(self, start_position_canvas:tuple[int, int])->None:
        self._box_start_position = start_position_canvas

    def end_box(self, end_position_canvas:tuple[int, int])->tuple[int,int,int,int]:
        if self._box_start_position is None:
            return None

        x1, y1 = self.canvas.canvas_to_image(*self._box_start_position)
        x2, y2 = self.canvas.canvas_to_image(*end_position_canvas)

        self._box_start_position = None
        self.canvas.delete("move_rectangle"+self.config.boxTag)

        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2),)
    

    def _on_mouse_move(self, event) -> None:
        self._current_mouse_canvas = (event.x, event.y)
        self.canvas.delete("move_rectangle"+self.config.boxTag)

        if self._box_start_position is not None:
            self.canvas.create_rectangle(self._box_start_position[0], self._box_start_position[1],
                event.x,event.y, tags="move_rectangle"+self.config.boxTag,)
            
    