import tkinter as tk

from shared.OperationResult import OperationResult
from invoice_annotator.enumerates.EventSource import EventSource


class ContextMenu(tk.Menu):

    #items --- slovnik, kde klic je jedno kontextové menu

    def __init__(self, parent, menus:dict[str, list[tuple[str, callable]]]):
        super().__init__(parent, tearoff=0)
        self.menus = menus

    def show(self, menuKey:str, position:tuple[int, int])->OperationResult:
        self._clear()

        if not menuKey in self.menus:
            return OperationResult(False, "Menu s tímto klíčem neexistuje")
        
        items: list[str, callable] = self.menus[menuKey]

        for label, command in items:
            self.add_command(label=label, command=lambda: command(position))

        try:
            self.tk_popup(position[0], position[1])
        finally:
            self.grab_release()

    def partial_redraw(self):
        self.full_redraw()

    def full_redraw(self):
        ...
    
    def _clear(self):
        self.delete(0, tk.END)