from dataclasses import dataclass

from invoice_annotator.enumerates.ContextMenuOptions import ContextMenuOptions
from invoice_annotator.model.GInvoice import GInvoice
from invoice_annotator.utils.GToken import GToken


class AppData:

    """Slouží pro statické uchovávání a držení proměnných napříč aplikací"""
    original_img_width:int = 0
    original_img_height:int = 0

    invoice: GInvoice = GInvoice()

    #canvas_width:int = 0
    #canvas_height:int = 0

    #scaled_img_width: int = 0
    #scaled_img_height: int = 0

    #canvas_img_scale:int  = 1
    #zoom:float = 1

    #img_path:str = ""

    #position:tuple[float, float] = [0 , 0]

    last_mouse_click_position:tuple[float, float]|None = None
    context_menu_clicked_option:ContextMenuOptions = ContextMenuOptions.OTHER

    @staticmethod
    def reset() -> None:

        AppData.original_img_width = 0
        AppData.original_img_height = 0

        #AppData.canvas_width = 0
        #AppData.canvas_height = 0

        #AppData.scaled_img_width = 0
        #AppData.scaled_img_height = 0


        #AppData.canvas_img_scale = 1
        #AppData.zoom = 1

        AppData.invoice = GInvoice()
