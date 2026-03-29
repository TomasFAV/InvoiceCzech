from __future__ import annotations
import tkinter as tk
from tkinter import Tk, ttk, messagebox
from tkinter import filedialog
from typing import Any

from pathlib import Path
from common.view.components.ExportInvoiceCanvas import ExportInvoiceCanvas
from invoice_annotator.controller.ExportPageController import ExportPageController
from common.view.components.InvoiceForm import Form, FormConfig
from common.invoice.OperationResult import OperationResult
from common.view.View import View


class ExportPage(View):
    """
    View (MVC) – skládá layout a deleguje práci na specializované komponenty.
    """

    def __init__(self, window:Tk, parent:Any, controller: ExportPageController, *args, **kwargs) -> None:
        super().__init__(window, parent, controller, *args, **kwargs)
        self.controller:ExportPageController = controller

        # --- layout ---
        self.export_invoice_canvas:ExportInvoiceCanvas|None = None
        self.invoice_form:Form|None = None

        self.form_data: dict[str, str] = self.controller.get_invoice_dict() #bude naplněno formulářem, předá se formuláři reference
        self.build()

    def build(self) -> None:
        # --- layout ---
        self._build_body()
        self._build_statusbar()


    # ---------- veřejné API (volá Controller) ----------
    def update_status(self, msg: str) -> None:
        self.status.config(text=msg)

    def partial_redraw(self) -> None:
        self.export_invoice_canvas.partial_redraw()
        self.invoice_form.partial_redraw()

    def full_redraw(self) -> None:
        self.export_invoice_canvas.full_redraw()
        self.invoice_form.full_redraw()

    def boot_up(self):        
        for key, value in self.controller.get_invoice_dict().items():
            self.form_data[key] = value
        
        self.export_invoice_canvas.load(self.controller.session.image_path, tokens=self.controller.get_tokens().passed_value)
        self.full_redraw()

    def fill_form_from_spans(self)->None:
        if not self.controller.session.image_path:
            messagebox.showwarning("Pozor","Není načtena žádná faktura")
            return 

        for key, value in self.controller.get_invoice_dict_from_spans().items():
            self.form_data[key] = value
        
        self.invoice_form.partial_redraw()

    def export_invoice(self):
        if not self.controller.session.image_path:
            messagebox.showwarning("Pozor","Není načtena žádná faktura")
            return 
        
        folder_path = filedialog.askdirectory(title="Vyber složku pro export")
        if not folder_path or folder_path == "":
            return  # uživatel zrušil
        
        result:OperationResult = self.controller.export_invoice(folder_path, form_data=self.form_data)
        if result.ok:
            if isinstance(result.passed_value, (str, Path)):
                self.update_status(f"Soubor {str(result.passed_value)} úspěšně anotován a exportován do: {str(result.passed_value)}")
                
                self.controller.session.reset()
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

        left_pane = ttk.Frame(self.panedwindow)
        self.export_invoice_canvas = ExportInvoiceCanvas(left_pane, self.window, self)
        self.export_invoice_canvas.pack(fill=tk.BOTH, expand=True)

        self.invoice_form = Form(
                    FormConfig("Faktura",
                       data=self.form_data, #nutné kvůli referenci, form_data budou formulářem naplněna
                       actions={
                           "Získat hodnoty ze spanů": self.fill_form_from_spans, 
                           "Exportovat fakturu": self.export_invoice,
                           "Vrátit se zpět": lambda:self.window.show_frame("HomePage")
                       }), self.window, self, self.panedwindow)

        self.panedwindow.add(left_pane, weight=50)
        self.panedwindow.add(self.invoice_form, weight=50)

    def _build_statusbar(self) -> None:
        self.status: ttk.Label = ttk.Label(self, text="", anchor="w", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
    