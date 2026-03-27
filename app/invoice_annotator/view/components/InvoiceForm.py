from dataclasses import dataclass
import tkinter as tk
from tkinter import Variable, ttk
from tkinter import messagebox
from tkinter import filedialog
from typing import Any, Callable, Iterable, List

from pyrsistent import v

from invoices_generator.core.bank import bank
from invoices_generator.core.company import company
from invoice_annotator.controller import Controller
from invoice_annotator.view import View
from invoice_annotator.view.interfaces.IDataAnnotator import IMainWindow
from invoice_annotator.view.components.Component import Component
from invoices_generator.core.enumerates.span_tags import SPAN_TAGS_TO_IGNORE, span_tags
from invoice_annotator.AppData import AppData
from shared.OperationResult import OperationResult


@dataclass
class FormConfig:
    label:str
    data:dict[str,str] #label:value
    actions:dict[str, callable] #label:function_to_call


class Form(Component):

    """
        Generická formulářová komponenta
    """

    def __init__(self, config:FormConfig, window:IMainWindow, parent_view:View, master):
        super().__init__(window, parent_view, master, padding=8)

        # ====== PROMĚNNÉ ======
        self.form_variables:dict[str, Variable] = {} #proměnné pro tkkinter pro input fieldy, label:tk.variable
        self.config: FormConfig = config

        # grid se bude roztahovat
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)
        
        self.init_variables()
        self.build_ui()

    def __sync_form_data(self, *args, **kwargs)->None:
        """
            volá se vždy při změně obsahu libovolného entry
        """
        for key, variable in self.form_variables.items():
            self.config.data[key] = variable.get()
            
    def init_variables(self)->None:
        self.form_variables:dict[str, Variable] = {}

        for key, value in self.config.data.items():
            variable: Variable = tk.StringVar(value=value)
            self.form_variables[key] = variable  
            variable.trace_add("write", self.__sync_form_data)


    def __build_row(self, label:str, variable:Variable, row:int)->None:
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w")
        ttk.Entry(self, textvariable=variable).grid(row=row, column=1, columnspan=3, sticky="ew", pady=2)

    def build_ui(self)->None:
        row:int = 0

        if self.config.label:
            ttk.Label(self, text="", font=("", 10, "bold")).grid(row=row, column=0, columnspan=4, sticky="w", pady=(0, 8))
            row += 1

        for key, variable in self.form_variables.items():
            self.__build_row(key, variable, row)
            row += 1

        # ====== BUTTONY ======

        for label, action in self.config.actions.items():
            ttk.Button(self, text=label, command=action).grid(row=row, column=0, columnspan=4, sticky="ew", pady=2)
            row += 1


    def get_values_from_spans_action(self)->None:
        #zavolam controller
        values:dict = AppData.invoice.to_json_donut()
        
        for key, value in values.items():
            self.form_variables[key].set(value)

    def partial_redraw(self)->None:
        self.full_redraw()

    def full_redraw(self)->None:
        for widget in self.winfo_children():
            widget.destroy()

        self.init_variables()
        self.build_ui()