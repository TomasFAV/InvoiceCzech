import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Iterable

from common.interfaces.IMainWindow import IMainWindow
from common.view.components.Component import Component
from common.enumerates.SegmentTag import SegmentTag
from common.enumerates.SpanTag import SpanTag
from common.enumerates.TokenTag import TokenTag


class ListBoxTabPanel(Component):
    """
    Levý panel se záložkami (Tokeny / Spany / Vztahy) a akcí „Přiřadit označení“.
    Zachovává veřejný `labels_list`, který vždy odkazuje na Listbox v aktuální záložce.
    """

    def __init__(self,master, tabs:dict[Any, list[Any]], select_handler: Callable[[TokenTag|SpanTag|SegmentTag], None]|None,
                 window:IMainWindow, parent_view):
        super().__init__(window, parent_view, master, padding=(8, 8))
        
        self.tabs = tabs
        self.lists:list[tk.Listbox]|None = list()

        self.items: list[Any] = list()
        self.current_list: tk.Listbox|None = None
        self.select_handler = select_handler

        self.build()
        self.bind_events()
    
    def partial_redraw(self):
        return self.build()

    def full_redraw(self):
        return self.build()

    def build(self):
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True, pady=(6, 8))

        for tab_label, items in self.tabs.items():
            tab = ttk.Frame(self._notebook)
            llist = self._make_listbox_with_scrollbar(tab)
            self._fill_listbox(llist, items)

            self.items.append(items)
            self.lists.append(llist)

            self._notebook.add(tab, text=str(tab_label))
            self.current_list: tk.Listbox = llist


    def bind_events(self)->None:
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        if self.select_handler is None:
            return
        
        assign_btn = ttk.Button(self, text="Přiřadit označení (Enter)", command=self.select)
        assign_btn.pack(fill=tk.X)

        # Zkratky (Enter / dvojklik) na všech listech -> on_assign
        for lb in self.lists:
            lb.bind("<Double-Button-1>", self.select)
        
        self.window.bind("<Return>", self.select)
        
        self._bind_arrow_tab_hotkeys()
        self._bind_tab_hotkeys()

    # ----------- Hotkeys 1/2/3 -----------

    def _bind_tab_hotkeys(self) -> None:
        self._hotkey_map: dict[str, int] = {}

        for idx in range(len(self.lists)):
            key = str(idx + 1)

            normal = f"<KeyPress-{key}>"
            keypad = f"<KeyPress-KP_{key}>"

            self._hotkey_map[key] = idx
            self._hotkey_map[f"KP_{key}"] = idx

            self.bind_all(normal, self._on_tab_hotkey, add="+")
            self.bind_all(keypad, self._on_tab_hotkey, add="+")

    # ----------- Hotkeys šipkami ← / → -----------
    def _bind_arrow_tab_hotkeys(self) -> None:
        # Bindujeme na celý app (stejně jako 1/2/3), ať to funguje odkudkoli.
        for pat in ("<KeyPress-Right>", "<KeyPress-Left>"):
            self.bind_all(pat, self._on_arrow_tab_nav, add="+")

    def _on_tab_hotkey(self, event) -> str | None:
        idx = self._hotkey_map.get(event.keysym)
        if idx is None:
            return None

        self.show_tab(idx)
        return "break"

    def _on_arrow_tab_nav(self, event) -> str | None:
        tabs = self._notebook.tabs()
        if not tabs:
            return None

        cur_idx = self._notebook.index(self._notebook.select())
        if event.keysym == "Right":
            new_idx = (cur_idx + 1) % len(tabs)  # wrap dopředu
        elif event.keysym == "Left":
            new_idx = (cur_idx - 1) % len(tabs)  # wrap dozadu
        else:
            return None

        self.show_tab(new_idx)
        return "break"  # zastaví další propagaci

    def show_tab(self, idx:int)->None:
        if(idx >= len(self.lists) or idx < 0 or 
           idx >= len(self._notebook.tabs())):
            return
        
        self._notebook.select(idx)
        widget = self.lists[idx]
        widget.focus_set()

        

    # ----------- Pomocné / interní -----------
    def _make_listbox_with_scrollbar(self, parent: ttk.Frame) -> tk.Listbox:
        wrap = ttk.Frame(parent)
        wrap.pack(fill=tk.BOTH, expand=True)

        lb = tk.Listbox(wrap, height=12, exportselection=False)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=lb.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        lb.configure(yscrollcommand=y_scroll.set)
        return lb

    def _fill_listbox(self, lb: tk.Listbox, labels: Iterable[str]) -> None:
        lb.delete(0, tk.END)
        for i, lbl in enumerate(labels):
            lb.insert(i, str(lbl))
            

    def _on_tab_changed(self, _event=None) -> None:
        # Zjisti, který tab je aktivní, a aktualizuj alias + source
        current_idx = self._notebook.index(self._notebook.select())
        self.current_list = self.lists[current_idx]

    def select(self, *args, **kwargs):
        """Do metody select_handler vrátí předaný objekt na který bylo kliknuto"""
        selection = self.current_list.curselection()
        if not selection:
            return False

        idx = selection[0]
        item = self.items[self._notebook.index(self._notebook.select())][idx]
        
        self.select_handler(item)
        
    