from abc import abstractmethod
import tkinter
from invoice_annotator.view.interfaces.IDataAnnotator import IMainWindow
from invoice_annotator.controller.Controller import Controller


class View(tkinter.Frame):
    
    def __init__(self, root:tkinter.Tk, parent:tkinter.Frame, controller:Controller,):
        tkinter.Frame.__init__(self, master=parent)
        self.controller = controller
        self.parent = parent
        self.window:IMainWindow = root

    @abstractmethod
    def build(self) -> None:
        ...

    @abstractmethod
    def partial_redraw(self) -> None:
        ...

    @abstractmethod
    def full_redraw(self) -> None:
        ...