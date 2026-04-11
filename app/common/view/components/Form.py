from dataclasses import dataclass
import tkinter as tk
from tkinter import Variable, ttk
from typing import Any, Callable


from common.view import View
from common.interfaces.IMainWindow import IMainWindow
from common.view.components.Component import Component


@dataclass
class FormConfig:
    label:str
    data:dict[str,str|dict[str, bool]] #label:value => tk.Entry nebo label:[value1, value2, ...] => ttk.combobox
    actions:dict[str, Callable] #label:function_to_call


class Form(Component):

    """
        Generická formulářová komponenta
    """

    def __init__(self, config:FormConfig, window:IMainWindow, parent_view:View, master):
        super().__init__(window, parent_view, master, padding=8)
        self._sync_enabled = True

        # ====== PROMĚNNÉ ======
        self.form_variables:dict[str, Variable] = {} #proměnné pro tkkinter pro input fieldy, label:tk.variable
        self.config: FormConfig = config

        # grid se bude roztahovat
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)
        
        self.init_variables()
        self.build_ui()

    def update_values(self, new_values:dict[str, Any]):
        self._sync_enabled = False
        for key, value in new_values.items():
            self.config.data[key] = value

            if key in self.form_variables:
                if isinstance(value, dict):
                    selected = next((option for option, checked in value.items() if checked), "")
                    self.form_variables[key].set(selected)
                else:
                    self.form_variables[key].set(value)
        self._sync_enabled = True

    def __sync_form_data(self, *args, **kwargs)->None:
        """
            volá se vždy při změně obsahu libovolného entry
        """
        if not self._sync_enabled:
            return
        
        for key, variable in self.form_variables.items():
            if isinstance(self.config.data[key], str):
                self.config.data[key] = variable.get()
            elif isinstance(self.config.data[key], dict):
                value: str = variable.get()
                for option, val in self.config.data[key].items():
                    if option == value:
                        self.config.data[key][option] = True
                    else:
                        self.config.data[key][option] = False

            
    def init_variables(self)->None:
        self.form_variables:dict[str, Variable] = {}

        for key, value in self.config.data.items():
            if isinstance(value, dict):
                selected = next((option for option, checked in value.items() if checked), "")
                variable = tk.StringVar(value=selected)
            else:
                variable = tk.StringVar(value=value)

            self.form_variables[key] = variable
            variable.trace_add("write", self.__sync_form_data)


    def __build_row(self, label:str, variable:Variable, row:int)->None:
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w")
        if(isinstance(self.config.data[label], str)):
            ttk.Entry(self, textvariable=variable).grid(row=row, column=1, columnspan=3, sticky="ew", pady=2)
        elif(isinstance(self.config.data[label], dict)):
            ttk.Combobox(self, values=[l for l, _ in self.config.data[label].items()], state="readonly", textvariable=variable)\
                .grid(row=row, column=1, columnspan=3, sticky="ew", pady=2)

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

    def partial_redraw(self)->None:
        self._sync_enabled = False
        for key, value in self.config.data.items():
            self.config.data[key] = value

            if key in self.form_variables:
                if isinstance(value, dict):
                    selected = next((option for option, checked in value.items() if checked), "")
                    self.form_variables[key].set(selected)
                else:
                    self.form_variables[key].set(value)
        self._sync_enabled = True

    def full_redraw(self)->None:
        for widget in self.winfo_children():
            widget.destroy()

        self.init_variables()
        self.build_ui()