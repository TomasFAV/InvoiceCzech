from __future__ import annotations
import tkinter as tk
from tkinter import Tk, ttk, messagebox

import tkinter
from tkinter import filedialog
from tkinter import simpledialog
from turtle import st
from typing import Any, List, Callable

from regex import F

from shared.OperationResult import OperationResult
from invoice_annotator.controller.HomePageController import HomePageController
from invoice_annotator.enumerates.ContextMenuOptions import ContextMenuOptions
from invoice_annotator.utils import GSegment
from invoices_generator.core.enumerates.segment_tags import segment_tags
from invoice_annotator.enumerates.DataSource import DataSource
from invoice_annotator.enumerates.EventSource import EventSource
from invoice_annotator.utils.GRelationship import GRelationship
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
from invoice_annotator.view.View import View
from invoice_annotator.AppData import AppData
from invoice_annotator.view.components.ImageCanvas import ImageCanvas
from invoice_annotator.view.components.LabelsPanel import LabelsPanel
from invoice_annotator.view.components.EntitiesPanel import EntitiesPanel
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.enumerates.token_tags import token_tags


class HomePage(View):
    """
    View (MVC) – skládá layout a deleguje práci na specializované komponenty.
    Sdílený stav (zoom, pozice, atd.) zůstává v AppData kvůli kompatibilitě s Controllerem.
    """

    def __init__(self, window:Tk, parent:Any, controller: HomePageController, *args, **kwargs) -> None:
        super().__init__(window, parent, controller, *args, **kwargs)
        self.controller:HomePageController = controller

        self.token_labels: List[token_tags] = list(token_tags)
        self.span_labels: List[span_tags] = list(span_tags)[1:]
        self.relationship_labels: List[relationship_types] = list(relationship_types)[1:]
        self.segment_labels: List[segment_tags] = list(segment_tags)

        # --- layout ---
        self.labels_panel:LabelsPanel|None = None
        self.image_canvas:ImageCanvas|None = None
        self.entities_panel:EntitiesPanel|None = None
    



        self.build()

        # klávesa Enter – přiřadit aktuální štítek
        self.window.bind("<Return>", self._set_tag)
        #binding acceleratoru
        self.window.bind_all("<Control-o>", self.open_invoice)
        self.window.bind_all("<Control-e>", self.export_invoice)
        self.window.bind_all("<Control-r>", self.reset_token_tags)
        self.window.bind_all("<Control-q>", self.destroy)

    def build(self) -> None:
        # --- layout ---
        self._build_menu()
        self._build_body()
        self._build_statusbar()
        self._build_context_menu()


    # ---------- veřejné API (volá Controller) ----------
    def update_status(self, msg: str) -> None:
        self.status.config(text=msg)

    # tyto tři metody delegují na ImageCanvas (zachováno API pro Controller)
    def display_img(self, img_path: str) -> None:
        self.image_canvas.display_img(img_path)

    def display_bounding_boxes(self) -> None:
        self.image_canvas.display_bounding_boxes()
        try:
            if getattr(AppData, "invoice", None) is not None:
                self.entities_panel.populate_spans(AppData.invoice)
        except Exception:
            pass

    def partial_redraw(self) -> None:
        try:
            if getattr(AppData, "invoice", None) is not None:
                self.entities_panel.populate_spans(AppData.invoice)
                self.entities_panel.populate_relationships(AppData.invoice)
        except Exception:
            pass

        self.image_canvas.partial_redraw()


    def open_invoice(self):
        self.window.show_frame("HomePage")
        
        file = tkinter.filedialog.askopenfile(filetypes=[("png","*.png"),("jpg","*.jpg")])
        if not file:
            return

        result: OperationResult = self.controller.open_invoice(file.name)
        if result.ok:
            if isinstance(result.passed_value, str):
                self.display_img(result.passed_value)
                self.partial_redraw()
                self.update_status(f"Načtena faktura: {result.passed_value}")
            else:
                messagebox.showwarning("Chyba","Neočekávaný výstup ve metodě open_invoice")
        else:
            messagebox.showwarning("Chyba","Operace se nezdařila")

    def export_invoice(self):
        #přepneme na export vokno
        self.window.show_frame("ExportPage")


    def reset_token_tags(self):
        result: OperationResult = self.controller.reset_token_tags()

        if result.ok:
            self.partial_redraw()
        else:
            messagebox.showerror("Chyba","Operace se nezdařila")

    # ---------- UI build ----------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.window)
        filemenu = tk.Menu(menubar, tearoff=0)

        filemenu.add_command(
            label="Otevřít sken...",
            command=lambda: self.open_invoice(),
            accelerator="Ctrl+O",
        )

        filemenu.add_command(
            label="Exportovat...",
            command=lambda: self.export_invoice(),
            accelerator="Ctrl+E",
        )

        filemenu.add_separator()

        filemenu.add_command(
            label="Resetovat všechny tagy tokenů",
            command=lambda: self.reset_token_tags(),
            accelerator="Ctrl+R"
        )

        filemenu.add_separator()

        filemenu.add_command(
            label="Konec",
            command=lambda: self.destroy(),
            accelerator="Ctrl+Q",
        )

        menubar.add_cascade(label="Soubor", menu=filemenu)
        self.window.config(menu=menubar)

    def _build_body(self) -> None:
        self.panedwindow = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.panedwindow.pack(fill=tk.BOTH, expand=True)

        # Levý panel: štítky
        self.labels_panel = LabelsPanel(self.panedwindow, self.token_labels, self.span_labels,
            self.relationship_labels, self.segment_labels, on_assign=lambda: self._set_tag(None),)

        # Střed: toolbar + canvas_view
        center = ttk.Frame(self.panedwindow, padding=(0, 8, 0, 8))

        # Canvas – delegujeme klik na akci kontroleru
        self.image_canvas = ImageCanvas(center,
                                       on_left_click=lambda pos: self.select(pos, self.labels_panel.get_current_source(), self.image_canvas.token_enabled_value.get(), self.image_canvas.span_enabled_value.get(), self.image_canvas.segment_enabled_value.get()),
                                       on_right_click= lambda pos_glob, pos_loc, event: self._show_context_menu(pos_glob, pos_loc, event),
                                       root=self)
        self.image_canvas.pack(fill=tk.BOTH, expand=True)

        # Pravý panel: entity
        self.entities_panel = EntitiesPanel(self.panedwindow, on_right_click= lambda pos_glob, pos_loc, event: self._show_context_menu(pos_glob, pos_loc, event), create_spans_event=self._create_spans_from_labeled_tokens)

        # vložit do panedwindow
        self.panedwindow.add(self.labels_panel, weight=25)
        self.panedwindow.add(center, weight=50)
        self.panedwindow.add(self.entities_panel, weight=25)

        

    #--------------------------------------context menu operace ---------------------------------------------------
    def reset_token_tag(self, token:GToken):
        AppData.context_menu_clicked_option = ContextMenuOptions.OTHER
        result:OperationResult = self.controller.reset_token(token)

        if result.ok:
            self.image_canvas.partial_redraw()
            self.entities_panel.redraw_current()
        else:
            messagebox.showerror("Chyba","Operace se nezdařila")

    def remove_token(self, token:GToken):
        AppData.context_menu_clicked_option = ContextMenuOptions.OTHER
        result:OperationResult = self.controller.remove_token(token)

        if result.ok:
            self.partial_redraw()
            self.entities_panel.redraw_current()
        else:
            messagebox.showerror("Chyba","Operace se nezdařila")

    def remove_span(self, span:GSpan):
        AppData.context_menu_clicked_option = ContextMenuOptions.OTHER
        result:OperationResult = self.controller.remove_span(span)

        if result.ok:
            self.image_canvas.partial_redraw()
            self.entities_panel.redraw_current()
        else:
            messagebox.showerror("Chyba","Operace se nezdařila")

    def remove_relationship(self, relationship: GRelationship):
        AppData.context_menu_clicked_option = ContextMenuOptions.OTHER
        result:OperationResult = self.controller.remove_relationship(relationship)

        if result.ok:
            self.entities_panel.redraw_current()
        else:
            messagebox.showerror("Chyba","Operace se nezdařila")

    def remove_segment(self, segment: GSegment):
        AppData.context_menu_clicked_option = ContextMenuOptions.OTHER
        result:OperationResult = self.controller.remove_segment(segment)

        if result.ok:
            self.image_canvas.partial_redraw()
            self.entities_panel.redraw_current()
        else:
            messagebox.showerror("Chyba","Operace se nezdařila")


    def create_token(self, mouse_position_local):
        self.image_canvas.context_menu_clicked_option = ContextMenuOptions.CREATE_TOKEN

        if self.image_canvas._create_start_canvas is None:
            self.image_canvas.begin_create_box(mouse_position_local)
            self.config(cursor="cross")
            return

        bbox = self.image_canvas.finish_create_box(mouse_position_local)
        if bbox is None:
            return

        text = simpledialog.askstring("Tvorba tokenu", "Jaký text má obsahovat token?")
        if not text:
            self.config(cursor="arrow")
            return

        result = self.controller.create_token(bbox, text)

        self.config(cursor="arrow")
        if result.ok:
            self.partial_redraw()
        else:
            messagebox.showerror("Chyba", "Operace se nezdařila")
    

    def create_segment(self, mouse_position_local):
        self.image_canvas.context_menu_clicked_option = ContextMenuOptions.CREATE_SEGMENT

        if self.image_canvas._create_start_canvas is None:
            self.image_canvas.begin_create_box(mouse_position_local)
            self.config(cursor="cross")
            return

        bbox = self.image_canvas.finish_create_box(mouse_position_local)
        if bbox is None:
            return


        result = self.controller.create_segment(bbox)

        self.config(cursor="arrow")
        if result.ok:
            self.partial_redraw()
        else:
            messagebox.showerror("Chyba", "Operace se nezdařila")

    #--------------------------------------context menu operace ---------------------------------------------------
    #---------------------------------------------KONEC------------------------------------------------------------
    # ---------- Pomocné ----------

    def _show_context_menu_canvas(self, mouse_position_global, mouse_position_local, event_source:EventSource):
        span = self.controller.get_span_by_bounding_box(mouse_position_local, self.image_canvas)
        token = self.controller.get_token_by_bounding_box(mouse_position_local, self.image_canvas)
        segment = self.controller.get_segment_by_bounding_box(mouse_position_local, self.image_canvas)

        if (self.image_canvas.span_enabled_value.get() and span):
            self._fill_span_context_menu(span)
        elif(self.image_canvas.token_enabled_value.get() and token):
            self._fill_token_context_menu(token)
        elif(self.image_canvas.segment_enabled_value.get() and segment):
            self._fill_segment_context_menu(segment)
        else:
            self._fill_create_object_menu(mouse_position_local)

    def _show_context_menu_entities_panel(self, mouse_position_global, mouse_position_local, event_source:EventSource):
            cur_item = self.entities_panel.tree.focus()
            cur_item = self.entities_panel.tree.item(cur_item)
            
            if(self.entities_panel._current_view == "spans"):
                if cur_item and cur_item['values'] and cur_item['values'][0] == "SPAN":
                    span: GSpan = [sp for sp in AppData.invoice._spans if sp.id == cur_item['values'][1]][0]
                    self._fill_span_context_menu(span)

                elif cur_item and cur_item['values'] and cur_item['values'][0] == "TOK":
                    token: GToken = [tk for tk in AppData.invoice._tokens if tk.id == cur_item['values'][1]][0]
                    self._fill_token_context_menu(token)

            elif(self.entities_panel._current_view == "relationships"):
                if cur_item and cur_item['tags'][0] == "SPAN":
                    span: GSpan = [sp for sp in AppData.invoice._spans if sp.id == cur_item['values'][1]][0]
                    self._fill_span_context_menu(span)

                elif cur_item and cur_item['tags'][0] == "RELATIONSHIP":
                    relationship: GRelationship = [rel for id, rel in enumerate(AppData.invoice._relationships) if id == cur_item['values'][1]][0]
                    self._fill_relationship_context_menu(relationship)
            else:
                messagebox.showerror("Error", "při stisknutí kolečka _view obsahuje neplatnou hodnotu")

    def _show_context_menu(self, mouse_position_global, mouse_position_local, event_source:EventSource) -> None:
        self._clear_context_menu()
        try:
            if(event_source == EventSource.IMAGE_CANVAS):
                self._show_context_menu_canvas(mouse_position_global, mouse_position_local, event_source)

            elif(event_source == EventSource.ENTITIES_PANEL):
                self._show_context_menu_entities_panel(mouse_position_global, mouse_position_local, event_source)

            elif(event_source == EventSource.LABELS_PANEL):
                ...

            self._ctx.tk_popup(mouse_position_global[0], mouse_position_global[1])
        finally:
            self._ctx.grab_release()

    # ---------- Události ----------

    def _set_tag(self, _event) -> bool:
        selection = self.labels_panel.labels_list.curselection()
        if not selection:
            return False

        idx = selection[0]
        result:OperationResult = OperationResult(False)
        if self.labels_panel.get_current_source() == DataSource.TOKENS:
            tag = list(token_tags)[idx]
            result: OperationResult = self.controller.set_selected_tokens_token_tag(tag)

        elif self.labels_panel.get_current_source() == DataSource.SPANS:
            tag = list(span_tags)[idx+1] #Kvůli vynechanému prvnímu prvku z enum
            result: OperationResult = self.controller.set_selected_tokens_span_tag(tag)
            
        elif self.labels_panel.get_current_source() == DataSource.RELATIONSHIP:
            tag = list(relationship_types)[idx+1] #Kvůli vynechanému prvnímu prvku z enum
            result: OperationResult = self.controller.set_selected_relationship_tag(tag)

        elif self.labels_panel.get_current_source() == DataSource.SEGMENTS:
            tag = list(segment_tags)[idx]
            result: OperationResult = self.controller.set_selected_segments_segment_tag(tag)


        if not result.ok or not self.sync_bounding_boxes_color():
                messagebox.showerror("Chyba","Operace se nezdařila")
                return False

        self.partial_redraw()
        return True

    #vytvoří automaticky ze všech tokenů, které mají tag b_něco samostatný span,
    #jestliže nejsou již obsažené v jiném spanu
    def _create_spans_from_labeled_tokens(self) -> None:
        self.controller.create_spans_from_labeled_tokens()

        self.partial_redraw()
        self.entities_panel.redraw_current()

    def sync_bounding_boxes_color(self) -> bool:
        return self.image_canvas.sync_bounding_boxes_color()
    
    def select(self, pos, source:DataSource, token_enabled_value:bool, span_enabled_value:bool, segment_enabled_value:bool)-> bool:
        result:OperationResult = self.controller.select(pos, source, token_enabled_value, span_enabled_value, segment_enabled_value,
                                                        self.image_canvas)
        
        if result.ok:
            self.sync_bounding_boxes_color()
            return True
        else:
            messagebox.showwarning(
                "Upozornění",
                "Musíte zvolit, zda chcete označovat tokeny/spany a mít zobrazené tokeny, "
                "nebo označovat vztahy a mít zobrazené spany."
            )
            return False
        


    ###################################################################

    def _build_statusbar(self) -> None:
        self.status: ttk.Label = ttk.Label(self, text="", anchor="w", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_context_menu(self) -> None:
        self._ctx = tk.Menu(self, tearoff=0)

    def _fill_token_context_menu(self, token:GToken) -> None:
        self._clear_context_menu()

        self._ctx.add_command(label="Resetovat tag tokenu", command=lambda: self.reset_token_tag(token))
        self._ctx.add_command(label="Odstranit token",  command=lambda: self.remove_token(token))

    def _fill_span_context_menu(self, span:GSpan) -> None:
        self._clear_context_menu()

        self._ctx.add_command(label="Odstranit Span", command=lambda: self.remove_span(span))

    def _fill_relationship_context_menu(self, relationship:GRelationship) -> None:
        self._clear_context_menu()

        self._ctx.add_command(label="Odstranit Vztah", command=lambda: self.remove_relationship(relationship))

    def _fill_segment_context_menu(self, segment:GSegment)->None:
        self._clear_context_menu()

        self._ctx.add_command(label="Odstranit Segment", command=lambda: self.remove_segment(segment))

    def _fill_create_object_menu(self, mouse_position_local) -> None:
        self._clear_context_menu()
        self._ctx.add_command(label="Vytvořit Token", 
                              command=lambda: self.create_token(mouse_position_local))
        self._ctx.add_command(label="Vytvořit Segment",
                              command=lambda: self.create_segment(mouse_position_local))

    def _clear_context_menu(self) -> None:
        self._ctx.delete(0, tk.END)