import tkinter as tk
from tkinter import ttk
from typing import Callable, Iterable, List

from invoices_generator.core.enumerates.segment_tags import segment_tags
from invoice_annotator.enumerates.DataSource import DataSource
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.enumerates.token_tags import token_tags


class LabelsPanel(ttk.Frame):
    """
    Levý panel se záložkami (Tokeny / Spany / Vztahy) a akcí „Přiřadit označení“.
    Zachovává veřejný `labels_list`, který vždy odkazuje na Listbox v aktuální záložce.
    """

    def __init__(
        self,
        master,
        token_labels: List[token_tags],
        span_labels: List[span_tags],
        relationship_labels: List[relationship_types],
        segment_labels: List[segment_tags],
        on_assign: Callable[[], None],
    ):
        super().__init__(master, padding=(8, 8))

        self._mark_data_source: DataSource = DataSource.TOKENS

        self.token_labels: List[token_tags] = token_labels
        self.span_labels: List[span_tags] = span_labels
        self.relationship_labels: List[relationship_types] = relationship_labels
        self.segment_labels: List[segment_tags] = segment_labels

        # Nadpis
        ttk.Label(self, text="Štítky", font=("", 10, "bold")).pack(fill=tk.X)

        # Notebook (taby)
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill=tk.BOTH, expand=True, pady=(6, 8))

        # --- Tab: Tokeny ---
        self._tab_tokens = ttk.Frame(self._notebook)
        self._notebook.add(self._tab_tokens, text="Tokeny")
        self._tokens_list = self._make_listbox_with_scrollbar(self._tab_tokens)

        # --- Tab: Spany ---
        self._tab_spans = ttk.Frame(self._notebook)
        self._notebook.add(self._tab_spans, text="Spany")
        self._spans_list = self._make_listbox_with_scrollbar(self._tab_spans)

        # --- Tab: Vztahy ---
        self._tab_rels = ttk.Frame(self._notebook)
        self._notebook.add(self._tab_rels, text="Vztahy")
        self._rels_list = self._make_listbox_with_scrollbar(self._tab_rels)

        # --- Tab: Segmenty ---
        self._tab_segments = ttk.Frame(self._notebook)
        self._notebook.add(self._tab_segments, text="Segmenty")
        self._segments_list = self._make_listbox_with_scrollbar(self._tab_segments)

        # Veřejný alias na aktuální listbox (kvůli kompatibilitě)
        self.labels_list: tk.Listbox = self._tokens_list  # defaultně první tab

        # Naplnění obsahu
        self._fill_listbox(self._tokens_list, [t.text for t in self.token_labels])
        self._fill_listbox(self._spans_list, [s.text for s in self.span_labels])
        self._fill_listbox(self._rels_list,  [r.text for r in self.relationship_labels])
        self._fill_listbox(self._segments_list,  [s.text for s in self.segment_labels])

        # Sync aliasu a zdroje při změně tabu
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Akční tlačítko
        assign_btn = ttk.Button(self, text="Přiřadit označení (Enter)", command=on_assign)
        assign_btn.pack(fill=tk.X)

        # Zkratky (Enter / dvojklik) na všech listech -> on_assign
        for lb in (self._tokens_list, self._spans_list, self._rels_list):
            lb.bind("<Double-Button-1>", lambda _e: on_assign())

        # --- HOTKEYS: čísla 1,2,3 pro přepínání tabů ---
        #self._bind_tab_hotkeys()
        self._bind_arrow_tab_hotkeys()

    # ----------- Hotkeys 1/2/3 -----------

    def _bind_tab_hotkeys(self) -> None:
        self._hotkey_patterns = (
            "<KeyPress-1>", "<KeyPress-2>", "<KeyPress-3>", "<KeyPress-4>",
            "<KeyPress-KP_1>", "<KeyPress-KP_2>", "<KeyPress-KP_3>", "<KeyPress-KP_4>",
        )
        for pat in self._hotkey_patterns:
            self.bind_all(pat, self._on_tab_hotkey, add="+")

    def _on_tab_hotkey(self, event) -> str | None:
        mapping = {"1": 0, "2": 1, "3": 2, "4": 3, "KP_1": 0, "KP_2": 1, "KP_3": 2, "KP_4": 3}
        idx = mapping.get(event.keysym)
        if idx is None:
            return None
        tabs = self._notebook.tabs()
        self._notebook.select(idx)
        self._focus_by_index(idx)
        return "break"

    # ----------- Hotkeys šipkami ← / → -----------
    def _bind_arrow_tab_hotkeys(self) -> None:
        # Bindujeme na celý app (stejně jako 1/2/3), ať to funguje odkudkoli.
        for pat in ("<KeyPress-Right>", "<KeyPress-Left>"):
            self.bind_all(pat, self._on_arrow_tab_nav, add="+")

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

        self._notebook.select(new_idx)
        self._focus_by_index(new_idx)
        return "break"  # zastaví další propagaci

    #zajišťuje focus na správný tab
    def _focus_by_index(self, idx: int) -> None:
        if idx == 0:
            self._tokens_list.focus_set()
        elif idx == 1:
            self._spans_list.focus_set()
        elif idx == 2:
            self._rels_list.focus_set()
        elif idx == 3:
            self._segments_list.focus_set()
        

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
            lb.insert(i, lbl)

    def _on_tab_changed(self, _event=None) -> None:
        # Zjisti, který tab je aktivní, a aktualizuj alias + source
        current = self._notebook.select()
        if current == str(self._tab_tokens):
            self.labels_list = self._tokens_list
            self._mark_data_source = DataSource.TOKENS
        elif current == str(self._tab_spans):
            self.labels_list = self._spans_list
            self._mark_data_source = DataSource.SPANS
        elif current == str(self._tab_rels):
            self.labels_list = self._rels_list
            self._mark_data_source = DataSource.RELATIONSHIP
        elif current == str(self._tab_segments):
            self.labels_list = self._segments_list
            self._mark_data_source = DataSource.SEGMENTS


    # ----------- Veřejné API -----------

    def get_current_source(self) -> DataSource:
        return self._mark_data_source
