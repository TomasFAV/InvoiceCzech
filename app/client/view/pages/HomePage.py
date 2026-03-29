from __future__ import annotations
import tkinter as tk
from tkinter import Tk, ttk, messagebox
from tkinter import filedialog
from typing import Any

from pathlib import Path
from common.models.ModelController import Model
from client.controller.HomePageController import HomePageController
from common.view.components.Menu import Menu
from common.view.components.ExportInvoiceCanvas import ExportInvoiceCanvas
from common.view.components.InvoiceForm import Form, FormConfig
from common.invoice.OperationResult import OperationResult
from common.view.View import View


class HomePage(View):
    """
    View (MVC) – skládá layout a deleguje práci na specializované komponenty.
    """

    def __init__(self, window:Tk, parent:Any, controller: HomePageController, *args, **kwargs) -> None:
        super().__init__(window, parent, controller, *args, **kwargs)
        self.controller:HomePageController = controller

        # --- layout ---
        self.export_invoice_canvas:ExportInvoiceCanvas|None = None
        self.invoice_form:Form|None = None

        self.form_data: dict[str, str] = self.controller.get_invoice_dict() #bude naplněno formulářem, předá se formuláři reference
        self.form_data["AI model"] = {
            Model.Bert.value:True,
            Model.LiLT.value:False,
            Model.LayoutLMV3.value:False,
            Model.Donut.value: False,
            Model.Pix2Struct.value: False
        }
        
        self.build()

    def build(self) -> None:
        # --- layout ---
        self._build_body()
        self._build_statusbar()
        self._build_menu()

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
        #nahraju data, která chci vyplnit formulářem
        for key, value in self.controller.get_invoice_dict().items():
            self.form_data[key] = value
        
        
        self.export_invoice_canvas.load(self.controller.session.image_path, tokens=self.controller.get_tokens().passed_value)
        self.full_redraw()

    def fill_form_from_mined_data(self)->None:
        if not self.controller.session.image_path:
            messagebox.showwarning("Pozor","Není načtena žádná faktura")
            return 
        
        
        model = Model.LiLT  # default

        for m in Model:
            if self.form_data["AI model"].get(m.value):
                model = m
                break

        for key, value in self.controller.extract_invoice_data_from_image(model=model).items():
            self.form_data[key] = value
        

        self.export_invoice_canvas.load_tokens(self.controller.get_tokens().passed_value)
        self.invoice_form.partial_redraw()

    # ---------- veřejné API (volá Controller) ----------

    def open_invoice(self, **kwargs):
        #self.window.show_frame("HomePage")
        
        file = filedialog.askopenfile(filetypes=[("png","*.png"),("jpg","*.jpg")])
        if not file:
            return

        result: OperationResult = self.controller.open_invoice(file.name)
        self.controller.session.image_path = Path(file.name)

        if result.ok:
            if isinstance(result.passed_value, str):
                self.export_invoice_canvas.load(result.passed_value, tokens=self.controller.get_tokens().passed_value)
                self.invoice_form.update_values(self.controller.get_invoice_dict())
                self.update_status(f"Načtena faktura: {result.passed_value}")
            else:
                messagebox.showwarning("Chyba","Neočekávaný výstup ve metodě open_invoice")
        else:
            messagebox.showwarning("Chyba","Operace se nezdařila")


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
                           "Vytěžit data pomocí AI": self.fill_form_from_mined_data, 
                           "Exportovat fakturu": self.export_invoice,
                       }), self.window, self, self.panedwindow)

        self.panedwindow.add(left_pane, weight=50)
        self.panedwindow.add(self.invoice_form, weight=50)

    def _build_statusbar(self) -> None:
        self.status: ttk.Label = ttk.Label(self, text="", anchor="w", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _build_menu(self) -> None:
        menubar = tk.Menu(self.window)
        filemenu = Menu(menubar,
        {
          "default":[
              ("Otevřít sken...", "OPEN", self.open_invoice),
              ("Konec", "EXIT", lambda *args, **kwargs: self.quit())
          ]                 
        })

        menubar.add_cascade(label="Soubor", menu=filemenu)
        self.window.config(menu=menubar)