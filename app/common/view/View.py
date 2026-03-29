from abc import ABC, abstractmethod
import tkinter
from tkinter.ttk import Frame
from common.interfaces.IMainWindow import IMainWindow
from common.controller.Controller import Controller


class View(Frame, ABC):
    
    def __init__(self, window:IMainWindow, parent:tkinter.Frame, controller:Controller|None = None, **kwargs):
        Frame.__init__(self, master=parent, **kwargs)
        self.controller = controller
        self.parent = parent
        self.window:IMainWindow = window

    @abstractmethod
    def build(self) -> None:
        ...

    @abstractmethod
    def partial_redraw(self) -> None:
        ...

    @abstractmethod
    def full_redraw(self) -> None:
        ...

    @abstractmethod
    def boot_up(self) -> None:
        ...