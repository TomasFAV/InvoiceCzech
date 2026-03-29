from dataclasses import dataclass
import tkinter as tk
from collections.abc import Callable
from typing import Any

from common.invoice.OperationResult import OperationResult

@dataclass
class MenuAction:
    name: str
    payload: dict[str, Any]

class Menu(tk.Menu):
    # items --- slovník, kde klíč je jedno kontextové menu

    def __init__(self, parent, menus: dict[str, list[tuple[str, str, Callable[[tuple[int, int]], object]]]]):
        super().__init__(parent, tearoff=0)
        self.menus = menus
        self._build()

    def hide(self):
        self.unpost()

    def show(self, menuKey: str, position: tuple[int, int], **kwargs) -> OperationResult:
        self._clear()

        self._build(menuKey, **kwargs)

        try:
            self.tk_popup(position[0], position[1])
        finally:
            self.grab_release()

        return OperationResult(True, "")

    def _build(self, menuKey="default", **kwargs):
        if menuKey not in self.menus:
            return OperationResult(False, "Menu s tímto klíčem neexistuje")

        items = self.menus[menuKey]

        for label, action, command in items:
            #vždy se předá jaké menu je otevřeno, jaká akce byla zvolena a potom všechny další parametry, které jsou třeba (kwargs)
            self.add_command(label=label, command=lambda cmd=command, act=action, key=menuKey: cmd(key=key, action=act, **kwargs))

    def partial_redraw(self):
        self.full_redraw()

    def full_redraw(self):
        ...

    def _clear(self):
        self.delete(0, tk.END)