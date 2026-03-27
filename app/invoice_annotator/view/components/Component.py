from tkinter import ttk 

from invoice_annotator.view.View import View
from invoice_annotator.controller.Controller import Controller
from invoice_annotator.view.interfaces.IDataAnnotator import IMainWindow


class Component(ttk.Frame):

    def __init__(self, window:IMainWindow, parent_view:View, master = None, **kwargs):
        super().__init__(master, **kwargs)

        self.window: IMainWindow = window
        self.parent_element = master
        self.parent_view = parent_view
    
    def full_redraw(self):
        ...
    
    def partial_redraw(self):
        ...