from tkinter import ttk
import _tkinter as tk
from typing import Any, Callable, Optional

from numpy import isin

from invoice_annotator.view.View import View
from invoice_annotator.view.interfaces.IDataAnnotator import IMainWindow
from invoice_annotator.view.components.Component import Component


class TreeObjectNotebook(Component):
    """
    Generický notebook panel se stromy.
    Každý tab je definovaný slovníkem:
        {
            tab_name: {
            "button":{
                "label":"...",
                "action":callabel,
            }
            "item_name":str,
            "items":[...]
            },
        }

    Každá položka z "items" se vypíše do stromu rekurzivně přes atributy objektu.
    """

    def __init__(self, master, tabs: dict[str, dict[str,Any]], window:IMainWindow, parent_view:View,) -> None:
        super().__init__(window, parent_view, master, padding=(8, 8))
        self.tabs = tabs
        self._notebook:ttk.Notebook|None = None  
        self.trees: list[ttk.Treeview] = list()
        self.tab_data: list[Any] = list()
        self.current_tree: ttk.Treeview|None = None
        self.build()

    def partial_redraw(self):
        return self.redraw_current()
    
    def full_redraw(self):
        return self.redraw_current()

    def build(self):
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True, pady=(6, 8)) 

        for tab_label, data in self.tabs.items():
            tab = ttk.Frame(self._notebook)
            
            self.trees.append(self.build_tree(tab))
            self.tab_data.append(data)
            self._notebook.add(tab, text=tab_label) 

            button:dict = data.get("button")
            if(button):
                ttk.Button(tab, text=button.get("label"), command=button.get("action"),).pack(fill="x", pady=(6, 0))

        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
    def build_tree(self, parent:ttk.Frame):
        tree = ttk.Treeview(parent, columns=("name", "value"),
                            show="tree headings", height=16)
        
        tree.heading("#0", text="")
        tree.heading("name", text="Položka")
        tree.heading("value", text="Hodnota")

        tree.column("#0", width=30, stretch=False)
        tree.column("name", anchor="center")
        tree.column("value", width=60, anchor="center")
        tree.pack(fill="both", expand=True)
        return tree
    
    def _on_tab_changed(self, _ev=None):
        current_idx = self._notebook.index(self._notebook.select())
        self.current_tree = self.trees[current_idx]
        self.populate_current()

    def redraw_current(self):
        self.populate_current()

    def clear(self) -> None:
        if self.current_tree is None:
            return
        for iid in self.current_tree.get_children():
            self.current_tree.delete(iid)

    def populate_current(self) -> None:
        current_idx = self._notebook.index(self._notebook.select())
        self.clear()

        current_tab_data = self.tab_data[current_idx]
        items = current_tab_data["items"]
        
        if callable(items):
            items = items()

        for item in items:
            self.insert_into_tree(self.current_tree, item, label=current_tab_data["item_name"])

    def insert_into_tree(self, tree:ttk.Treeview, item: Any, parent:str = "", label:str=""):
        

        #primitivní datový typ
        if isinstance(item, (str, int, float)):
            tree.insert(parent, "end", values=(label, item))
        
        elif isinstance(item, list):
            parent = tree.insert(parent, "end", values=(label, ""))
            for sub_item in item:
                self.insert_into_tree(tree,sub_item, parent)
            
        elif isinstance(item, dict):
            parent = tree.insert(parent, "end", values=(label, ""))
            for name, value in item.items():
                self.insert_into_tree(tree, value, parent, label=name)

        elif isinstance(item, object):
            parent = tree.insert(parent, "end", values=("Třída", ""))
            for name, value in item.__dict__:
                self.insert_into_tree(tree, value, parent, label=name)


