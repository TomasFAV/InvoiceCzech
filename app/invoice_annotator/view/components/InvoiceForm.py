import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
from typing import Callable, Iterable, List

from invoices_generator.core.bank import bank
from invoices_generator.core.company import company
from invoice_annotator.controller import Controller
from invoice_annotator.view import View
from invoice_annotator.view.interfaces.IDataAnnotator import IMainWindow
from invoice_annotator.view.components.Component import Component
from invoices_generator.core.enumerates.span_tags import SPAN_TAGS_TO_IGNORE, span_tags
from invoice_annotator.AppData import AppData
from shared.OperationResult import OperationResult



class InvoiceForm(Component):

    def __init__(self,  window:IMainWindow, controller:Controller, parent_view:View, master, export_invoice:Callable, leave:Callable):
        super().__init__(window, controller, parent_view, master, padding=8)

        # ====== PROMĚNNÉ ======
        self.variables = {}

        # grid se bude roztahovat
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)

        self.leave = leave
        self.export_invoice = export_invoice

        

    def init_variables(self):
        self.variables = {}

        for span_tag in list(span_tags):
            if span_tag in SPAN_TAGS_TO_IGNORE or span_tag == span_tags.O:
                continue
            self.variables[span_tag.text] = tk.StringVar()
        

    def __build_row(self, label, variable, row):
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=variable).grid(row=row, column=1, columnspan=3, sticky="ew", pady=2)

    def build_ui(self):
        row = 0

        ttk.Label(self, text="Faktura", font=("", 10, "bold"))\
            .grid(row=row, column=0, columnspan=4, sticky="w", pady=(0, 8))
        row += 1

        for key, variable in self.variables.items():
            self.__build_row(key, variable, row)
            row += 1

        # ====== BUTTONY ======

        ttk.Button(self, text="Získat hodnoty dle spanů", command=self.get_values_from_spans_action)\
            .grid(row=row, column=0, columnspan=4, sticky="ew", pady=2)
        row += 1

        ttk.Button(self, text="Exportovat anotovanou fakturu", command=self.export_invoice_action)\
            .grid(row=row, column=0, columnspan=4, sticky="ew", pady=2)

        row += 1

        ttk.Button(self, text="Opustit", command=self.leave_action)\
            .grid(row=row, column=0, columnspan=4, sticky="ew", pady=2)


    def get_values_from_spans_action(self):
        #zavolam controller
        values:dict = AppData.invoice.to_json_donut()
        
        for key, value in values.items():
            self.variables[key].set(value)


    def export_invoice_action(self):
        #naplnim daty fakturu ze ktere se následně provede export

        AppData.invoice.invoice_number = self.variables["invoice_number"].get()
        AppData.invoice.variable_symbol = self.variables["variable_symbol"].get()
        AppData.invoice.const_symbol = self.variables["const_symbol"].get()
        AppData.invoice.issue_date = self.variables["issue_date"].get()
        AppData.invoice.taxable_supply_date = self.variables["taxable_supply_date"].get()
        AppData.invoice.due_date = self.variables["due_date"].get()
        AppData.invoice.total_price = self.variables["total"].get()
        AppData.invoice.IBAN = self.variables["iban"].get()
        
        AppData.invoice.bank_account = bank("", "", self.variables["bic"].get())

        AppData.invoice.supplier = company("","","","","","",
                                           self.variables["supp_register_id"].get(),
                                           self.variables["supp_tax_id"].get())

        AppData.invoice.customer = company("","", "", "", "", "",
                                           self.variables["cust_register_id"].get(),
                                           self.variables["cust_tax_id"].get())


        AppData.invoice.payment_type = self.variables["payment_type"].get()
        AppData.invoice.bank_account_number = self.variables["bank_account_number"].get()

        self.export_invoice()


    def leave_action(self):
        self.leave()

    def partial_redraw(self):
        self.variables["invoice_number"].set(AppData.invoice.invoice_number)
        self.variables["variable_symbol"].set(AppData.invoice.variable_symbol)
        self.variables["const_symbol"].set(AppData.invoice.const_symbol)

        self.variables["issue_date"].set(AppData.invoice.issue_date)
        self.variables["taxable_supply_date"].set(AppData.invoice.taxable_supply_date)
        self.variables["due_date"].set(AppData.invoice.due_date)
        self.variables["total"].set(AppData.invoice.total_price)
        
        self.variables["iban"].set(AppData.invoice.IBAN)
        self.variables["bic"].set(AppData.invoice.bank_account.BIC)

        self.variables["supp_register_id"].set(AppData.invoice.supplier.register_id)
        self.variables["supp_tax_id"].set(AppData.invoice.supplier.tax_id)

        self.variables["cust_register_id"].set(AppData.invoice.customer.register_id)
        self.variables["cust_tax_id"].set(AppData.invoice.customer.tax_id)


        self.variables["payment_type"].set(AppData.invoice.payment_type)
        self.variables["bank_account_number"].set(AppData.invoice.bank_account_number)

    def full_redraw(self):
        for widget in self.winfo_children():
            widget.destroy()

        self.init_variables()
        self.build_ui()
        self.partial_redraw()
    