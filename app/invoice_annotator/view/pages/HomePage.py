from __future__ import annotations
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import tkinter
from tkinter import simpledialog
from common.invoice.models.GSegment import GSegment
from common.invoice.models.GSpan import GSpan
from common.invoice.models.GToken import GToken
from common.interfaces.IMainWindow import IMainWindow
from common.utils.consts import CREATE_SEGMENT, CREATE_TOKEN, REMOVE, RESET, SEGMENT_TAG, SPAN_TAG, TOKEN_TAG
from common.view.components.InvoiceCanvas import InvoiceCanvas, InvoiceCanvasConfig
from common.view.components.TreeObjectNotebook import TreeObjectNotebook
from common.view.components.ListBoxTabPanel import ListBoxTabPanel
from common.view.components.Menu import Menu
from common.invoice.OperationResult import OperationResult
from invoice_annotator.controller.HomePageController import HomePageController
from common.enumerates.SegmentTag import SegmentTag
from common.enumerates.DataSource import DataSource
from common.view.View import View
from common.enumerates.SpanTag import SpanTag
from common.enumerates.TokenTag import TokenTag


class HomePage(View):
    """
    View (MVC) – skládá layout a deleguje práci na specializované komponenty.
    """

    def __init__(self, window:IMainWindow, parent:ttk.Frame, controller: HomePageController, *args, **kwargs) -> None:
        super().__init__(window, parent, controller, *args, **kwargs)
        self.controller:HomePageController = controller

        # --- layout ---
        self.labels_panel:ListBoxTabPanel|None = None
        self.invoice_canvas:InvoiceCanvas|None = None
        self.entities_panel:TreeObjectNotebook|None = None
        self.context_menu: Menu|None = None

        self.build()

    def partial_redraw(self) -> None:
        self.entities_panel.redraw_current()
        self.invoice_canvas.partial_redraw()

    def full_redraw(self) -> None:
        self.entities_panel.redraw_current()
        self.invoice_canvas.full_redraw()

    def boot_up(self):
        self.invoice_canvas.load(self.controller.session.image_path, tokens=self.controller.get_tokens().passed_value,
                                 spans=self.controller.get_spans().passed_value, segments=self.controller.get_segments().passed_value)
                                 
        self.full_redraw()

    def build(self) -> None:
        # --- layout ---
        self._build_body()
        self._build_statusbar()
        self._build_menu()


    # ---------- veřejné API (volá Controller) ----------

    def open_invoice(self, **kwargs):
        self.window.show_frame("HomePage")
        
        file = tkinter.filedialog.askopenfile(filetypes=[("png","*.png"),("jpg","*.jpg")])
        if not file:
            return

        result: OperationResult = self.controller.open_invoice(file.name)
        self.controller.session.image_path = Path(file.name)

        if result.ok:
            if isinstance(result.passed_value, str):
                self.invoice_canvas.load(result.passed_value, tokens=self.controller.get_tokens().passed_value,
                                         spans=self.controller.get_spans().passed_value, segments=self.controller.get_segments().passed_value)
                self.entities_panel.redraw_current()
                self.update_status(f"Načtena faktura: {result.passed_value}")
            else:
                messagebox.showwarning("Chyba","Neočekávaný výstup ve metodě open_invoice")
        else:
            messagebox.showwarning("Chyba","Operace se nezdařila")

    def export_invoice(self, **kwargs):
        #přepneme na export vokno
        self.window.show_frame("ExportPage")

    #--------------------------------------  Event handlery ---------------------------------------------------
    def left_click_handler_object_collision(self, tag:str, id:int, mouse_click_canvas_position:tuple[int,int], **kwargs) -> None:
        if(tag == TOKEN_TAG):
            result = self.controller.toogle_token(id)
        elif(tag == SPAN_TAG):
            result = self.controller.toogle_span(id)
        elif(tag == SEGMENT_TAG):
            result = self.controller.toogle_segment(id)

        if not result.ok:
            messagebox.showerror("Chyba", "Chyba v left_click_handleru")

        self.invoice_canvas.partial_redraw()

    def left_click_handler_no_object_collision(self, mouse_click_canvas_position:tuple[int,int], **kwargs):
        result = self.invoice_canvas.end_token_box_creation(mouse_click_canvas_position)
        if(result.passed_value):
            text = simpledialog.askstring("Vložte", "Co má token obsahovat:", parent=self)
            self.controller.create_token(result.passed_value, text)
        
        result = self.invoice_canvas.end_segment_box_creation(mouse_click_canvas_position)
        if(result.passed_value):
            self.controller.create_segment(result.passed_value)
        
        self.invoice_canvas.partial_redraw()

    def select_handler(self, tag:TokenTag|SpanTag|SegmentTag) -> None:
        if(isinstance(tag, TokenTag)):
            result = self.controller.apply_tag_to_token_selection(tag)
        elif(isinstance(tag, SpanTag)):
            result = self.controller.apply_tag_to_span_selection(tag)
        elif(isinstance(tag, SegmentTag)):
            result = self.controller.apply_tag_to_segment_selection(tag)
        
        if not result.ok:
                messagebox.showerror("Chyba", "Chyba v select_handleru")

        self.entities_panel.redraw_current()
        self.invoice_canvas.partial_redraw()

    def context_menu_handler(self, key:str|None, action:str|None, id:int|None, mouse_click_canvas_position:tuple[int, int], **kwargs)->None:
        if action == None:
            return

        if(key == TOKEN_TAG):
            token:GToken = self.controller.get_token_by_id(id).passed_value
            if(action == RESET):
                self.controller.reset_token(token)
            elif(action == REMOVE):
                self.controller.remove_token(token)

        elif(key == SPAN_TAG):
            span:GSpan = self.controller.get_span_by_id(id).passed_value
            if(action == REMOVE):
                self.controller.remove_span(span)

        elif(key == SEGMENT_TAG):
            segment: GSegment = self.controller.get_segment_by_id(id).passed_value
            if(action == REMOVE):
                self.controller.remove_segment(segment)

        else:
            if(action == CREATE_TOKEN):
                self.invoice_canvas.begin_token_box_creation(mouse_click_canvas_position)
            elif(action == CREATE_SEGMENT):
                self.invoice_canvas.begin_segment_box_creation(mouse_click_canvas_position)


        self.entities_panel.redraw_current()
        self.invoice_canvas.partial_redraw()

    #-------------------------------------- Event handlery---------------------------------------------------
    #---------------------------------------------KONEC------------------------------------------------------------
    # ---------- Pomocné ----------

    #vytvoří automaticky ze všech tokenů, které mají tag b_něco samostatný span,
    #jestliže nejsou již obsažené v jiném spanu
    def create_spans_from_annotated_tokens(self) -> None:
        self.controller.create_spans_from_annotated_tokens()

        self.entities_panel.redraw_current()
        self.invoice_canvas.partial_redraw()

    def update_status(self, msg: str) -> None:
        self.status.config(text=msg)    


    def reset_token_tags(self, **kwargs):
        result: OperationResult = self.controller.reset_token_tags()

        if result.ok:
            self.entities_panel.redraw_current()
            self.invoice_canvas.partial_redraw()
        else:
            messagebox.showerror("Chyba","Operace se nezdařila")
    # ---------- UI build ----------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.window)
        filemenu = Menu(menubar,
        {
          "default":[
              ("Otevřít sken...", "OPEN", self.open_invoice),
              ("Exportovat...", "EXPORT", self.export_invoice),
              ("Resetovat všechny tagy tokenů", "RESET", self.reset_token_tags),
              ("Konec", "EXIT", lambda *args, **kwargs: self.quit())
          ]                 
        })

        menubar.add_cascade(label="Soubor", menu=filemenu)
        self.window.config(menu=menubar)

    def _build_body(self) -> None:
        self.panedwindow = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.panedwindow.pack(fill=tk.BOTH, expand=True)

        self.labels_panel = ListBoxTabPanel(self.panedwindow, 
                                            {
                                                DataSource.TOKENS: [tag for tag in list(TokenTag)],
                                                DataSource.SPANS: [tag for tag in list(SpanTag)[1:]],
                                                DataSource.SEGMENTS: [tag for tag in list(SegmentTag)]
                                            },select_handler=self.select_handler, window=self.window, parent_view=self)

        # Střed: toolbar + canvas_view
        center = ttk.Frame(self.panedwindow, padding=(0, 8, 0, 8))
        self.invoice_canvas = InvoiceCanvas(center, self.window, self, InvoiceCanvasConfig(leftClickHandlerObjectCollision=self.left_click_handler_object_collision,
                                                                                           leftClickHandlerNoObjectCollision=self.left_click_handler_no_object_collision, 
                                                                                           contextMenuHandler=self.context_menu_handler))
        self.invoice_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Pravý panel: entity
        self.entities_panel = TreeObjectNotebook(
            master=self.panedwindow,
            tabs={
                "spany":{ 
                    "item_name": "span",
                    "items": lambda: [{
                        "id":span.id,
                        "tag":span.tag.text,
                        "tokens":[self.controller.get_token_by_id(tok_idx).passed_value.text for tok_idx in span.tokens]
                   } for span in self.controller.get_spans().passed_value],
                    "button":{
                        "label": "vytvořit spany z označených tokenů",
                        "action": self.create_spans_from_annotated_tokens
                    }
                   }
                },
                window=self.window,
                parent_view=self
        )
        
        self.panedwindow.add(self.labels_panel, weight=25)
        self.panedwindow.add(center, weight=50)
        self.panedwindow.add(self.entities_panel, weight=25)

    def _build_statusbar(self) -> None:
        self.status: ttk.Label = ttk.Label(self, text="", anchor="w", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)