from __future__ import annotations
import tkinter as tk
from tkinter import Tk, ttk, messagebox

import tkinter
from tkinter import filedialog
from turtle import st
from typing import Any, List, Callable

from regex import F

from invoice_annotator.controller.ExportPageController import ExportPageController
from invoice_annotator.view.components.InvoiceForm import InvoiceForm
from shared.OperationResult import OperationResult
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


class ExportPage(View):
    """
    View (MVC) – skládá layout a deleguje práci na specializované komponenty.
    Sdílený stav (zoom, pozice, atd.) zůstává v AppData kvůli kompatibilitě s Controllerem.
    """

    def __init__(self, window:Tk, parent:Any, controller: ExportPageController, *args, **kwargs) -> None:
        super().__init__(window, parent, controller, *args, **kwargs)
        self.controller:ExportPageController = controller

        self.token_labels: List[token_tags] = list(token_tags)
        self.span_labels: List[span_tags] = list(span_tags)[1:]
        self.relationship_labels: List[relationship_types] = list(relationship_types)[1:]
        self.segment_labels: List[segment_tags] = list(segment_tags)

        # --- layout ---
        self.image_canvas:ImageCanvas|None = None




        self.build()

    def build(self) -> None:
        # --- layout ---
        self._build_body()
        self._build_statusbar()


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

    def display_text(self) -> None:
        self.image_canvas.display_text()

    def partial_redraw(self) -> None:
        self.image_canvas.partial_redraw()
        self.invoice_form.partial_redraw()

    def full_redraw(self) -> None:
        self.image_canvas.full_redraw()
        self.invoice_form.full_redraw()


    def export_invoice(self):
        if (not AppData.invoice or len(AppData.invoice._spans) == 0):
            messagebox.showwarning("Chyba", "Snažíte se exportovat prázdnou fakturu.")
            return

        folder_path = filedialog.askdirectory(title="Vyber složku pro export")
        if not folder_path or folder_path == "":
            return  # uživatel zrušil
        
        result:OperationResult = self.controller.export_invoice(folder_path)
        if result.ok:
            if isinstance(result.passed_value, str):
                self.update_status(f"Soubor {result.passed_value} úspěšně anotován a exportován do: {result.passed_value}")
                AppData.reset()
                self.display_img(None)
                self.partial_redraw()
                self.window.show_frame("HomePage")
            else:
                messagebox.showwarning("Chyba","Neočekávaný výstup ve metodě export_invoice")
        else:
            messagebox.showwarning("Chyba","Operace se nezdařila")

    # ---------- UI build ----------

    def _build_body(self) -> None:
        self.panedwindow = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        self.panedwindow.pack(fill=tk.BOTH, expand=True)

        # Střed: toolbar + canvas_view
        center = ttk.Frame(self.panedwindow, padding=(0, 8, 0, 8))

        # Canvas – delegujeme klik na akci kontroleru
        self.image_canvas = ImageCanvas(center,
                                       on_left_click=lambda: None(),
                                       on_right_click=lambda: None(),
                                       root=self)
        self.image_canvas.pack(fill=tk.BOTH, expand=True)


        # Pravý panel: entity
        self.invoice_form = InvoiceForm(self.window, self.controller, self, self.panedwindow,
                                         export_invoice= self.export_invoice,
                                         leave=lambda: self.window.show_frame("HomePage"))

        # vložit do panedwindow
        self.panedwindow.add(center, weight=50)
        self.panedwindow.add(self.invoice_form, weight=50)

        self.after(0, self._set_initial_sashes)

    def _set_initial_sashes(self) -> None:
        # Počkej, až bude mít panedwindow nenulovou šířku
        w = self.panedwindow.winfo_width()
        if w <= 1:
            self.after(50, self._set_initial_sashes)
            return
        # Sash 0 mezi 1. a 2. pane na 50 %, sash 1 mezi 2. pane na 50 %
        self.panedwindow.sashpos(0, int(w * 0.5))

    def _build_statusbar(self) -> None:
        self.status: ttk.Label = ttk.Label(self, text="", anchor="w", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)


    #--------------------------------------context menu operace ---------------------------------------------------
    #---------------------------------------------KONEC------------------------------------------------------------
    

    def sync_bounding_boxes_color(self) -> bool:
        return self.image_canvas.sync_bounding_boxes_color()
    
    def select(self, pos, source:DataSource, token_enabled_value:bool, span_enabled_value:bool, segment_enabled_value:bool)-> bool:
        result:OperationResult = self.controller.select(pos, source, token_enabled_value, span_enabled_value, segment_enabled_value)
        
        if result.ok:
            self.sync_bounding_boxes_color()
            return True
        else:
            messagebox.showerror("Chyba","Operace se nezdařila")
            return False