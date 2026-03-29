from tkinter import ttk 

from common.view.View import View
from common.controller.Controller import Controller
from common.interfaces.IMainWindow import IMainWindow


class Component(ttk.Frame):

    def __init__(self, window:IMainWindow, parent_view:View, master = None, **kwargs):
        super().__init__(master, **kwargs)

        self.window: IMainWindow = window
        self.parent_element = master
        self.parent_view = parent_view

        ttk.Style().map("TCombobox",
            fieldbackground=[("readonly", "white")],
            selectbackground=[("readonly", "white")],
            selectforeground=[("readonly", "black")],
            highlightcolor=[("focus", "white")],
            lightcolor=[("focus", "white")],
            bordercolor=[("focus", "white")]
        )
    
    def full_redraw(self):
        ...
    
    def partial_redraw(self):
        ...