from tkinter import ttk, messagebox
import tkinter as tk
from typing import Optional, Callable

from invoice_annotator.AppData import AppData
from invoice_annotator.enumerates.DataSource import DataSource
from invoice_annotator.enumerates.EventSource import EventSource
from invoice_annotator.model.GInvoice import GInvoice
from invoice_annotator.utils.GRelationship import GRelationship
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
from invoices_generator.core.enumerates.relationship_types import relationship_types


class EntitiesPanel(ttk.Frame):
    """Pravý panel s přehledem entit (Treeview) — ve dvou tabech."""

    def __init__(
        self,
        master,
        on_left_click: Optional[Callable[[tuple[int, int]], None]] = None,
        on_middle_click: Optional[
            Callable[[tuple[int, int], tuple[int, int], EventSource], None]
        ] = None,
        on_right_click: Optional[Callable[[tuple[int, int]], None]] = None,
        create_spans_event: Optional[Callable[[], None]] = None,
    ):
        super().__init__(master, padding=(8, 8))

        ttk.Label(self, text="Entity", font=("", 10, "bold")).pack(anchor="w", pady=(0, 4))

        self._on_left_click = on_left_click
        self._on_right_click = on_right_click
        self._on_middle_click = on_middle_click
        self._create_spans_event = create_spans_event

        # --- Notebook (tabs) ---
        self._notebook = ttk.Notebook(self)
        self._notebook.pack(fill="both", expand=True)

        # ===== Tab: Spany =====
        self._tab_spans = ttk.Frame(self._notebook)
        self._notebook.add(self._tab_spans, text="Spany")

        # obal pro strom + tlačítko
        spans_body = ttk.Frame(self._tab_spans)
        spans_body.pack(fill="both", expand=True)

        self.tree_spans: ttk.Treeview = self._build_span_tree(spans_body)
        # tlačítko je přímo v tab "Spany"
        ttk.Button(
            spans_body,
            text="Vytvořit spany na základě označených tokenů",
            command=self._create_spans_event,
        ).pack(fill=tk.X, pady=(6, 0))

        # ===== Tab: Vztahy =====
        self._tab_relationships = ttk.Frame(self._notebook)
        self._notebook.add(self._tab_relationships, text="Vztahy")
        self.tree_relationships: ttk.Treeview = self._build_relationship_tree(self._tab_relationships)

        # Alias na aktuální strom (kvůli kompatibilitě)
        self.tree: Optional[ttk.Treeview] = self.tree_spans
        self._current_view: str = "spans"

        # Bindy na obou stromech
        self._bind_events(self.tree_spans)
        self._bind_events(self.tree_relationships)

        # Reakce na přepnutí tabu
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Inicialní naplnění
        self.redraw_current()

    # ---------- události a pomocné ----------

    def _on_tab_changed(self, _ev=None):
        current = self._notebook.select()
        if current == str(self._tab_spans):
            self.tree = self.tree_spans
            self._current_view = "spans"
            self.populate_spans(AppData.invoice)
        else:
            self.tree = self.tree_relationships
            self._current_view = "relationships"
            self.populate_relationships(AppData.invoice)

    def _bind_events(self, tree: ttk.Treeview):
        for seq in ("<Button-1>", "<Button-2>", "<Button-3>", "<Control-Button-1>"):
            tree.bind(seq, self._focus_item_under_mouse, add="+")
        tree.bind("<Button-2>", self._on_middle_press, add="+")
        tree.bind("<Button-3>", self._on_right_press, add="+")

    def _focus_item_under_mouse(self, event):
        tree: ttk.Treeview = event.widget
        iid = tree.identify_row(event.y)
        if iid:
            tree.selection_set(iid)
            tree.focus(iid)
            tree.see(iid)
        else:
            for sel in tree.selection():
                tree.selection_remove(sel)
            tree.focus("")

    # ---------- veřejné přepínače pohledu (kompatibilita) ----------

    def show(self, source: DataSource):
        if source == DataSource.RELATIONSHIP:
            self._notebook.select(self._tab_relationships)
        else:
            self._notebook.select(self._tab_spans)

    def redraw_current(self):
        if self._current_view == "spans":
            self.populate_spans(AppData.invoice)
        elif self._current_view == "relationships":
            self.populate_relationships(AppData.invoice)
        else:
            messagebox.showerror(title="Error", message="Chyba v proměnné _current_view")

    # ---------- stavba stromů ----------

    def _build_span_tree(self, parent: ttk.Frame) -> ttk.Treeview:
        tree = ttk.Treeview(parent, columns=("kind", "id", "label", "info"),
                            show="tree headings", height=16)
        tree.heading("#0", text="")
        tree.heading("kind", text="Druh")
        tree.heading("id", text="ID")
        tree.heading("label", text="Štítek/Tag")
        tree.heading("info", text="Info")

        tree.column("#0", width=30, stretch=False)
        tree.column("kind", width=60, anchor="center")
        tree.column("id", width=60, anchor="center")
        tree.column("label", width=140, anchor="w")
        tree.column("info", width=220, anchor="w")
        tree.pack(fill="both", expand=True)
        return tree

    def _build_relationship_tree(self, parent: ttk.Frame) -> ttk.Treeview:
        tree = ttk.Treeview(parent, columns=("kind", "id", "info"),
                            show="tree headings", height=16)
        tree.heading("#0", text="")
        tree.heading("kind", text="Typ")
        tree.heading("id", text="ID")
        tree.heading("info", text="Info")

        tree.column("#0", width=30, stretch=False)
        tree.column("kind", width=100, anchor="center")
        tree.column("id", width=60, anchor="center")
        tree.column("info", width=300, anchor="w")
        tree.pack(fill="both", expand=True)
        return tree

    # ---------- plnění daty ----------

    def clear(self) -> None:
        if self.tree is None:
            return
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def populate_spans(self, invoice: GInvoice) -> None:
        tree = self.tree_spans
        for iid in tree.get_children():
            tree.delete(iid)

        if not invoice or not getattr(invoice, "_spans", None):
            return

        tokens = getattr(invoice, "_tokens", [])
        for sid, span in enumerate(invoice._spans):
            tag_name = span.tag.name
            info = f"skládá se z {len(span.tokens)} tokenů"
            parent = tree.insert("", "end", values=("SPAN", span.id, tag_name, info))
            for token_id in span.tokens:
                tok: GToken = AppData.invoice.get_token_by_id(token_id)
                tok_tag = getattr(tok.tag, "name", str(tok.tag))
                tok_text = getattr(tok, "text", "")
                tree.insert(parent, "end", values=("TOK", tok.id, tok_tag, tok_text))

    def populate_relationships(self, invoice: GInvoice) -> None:
        tree = self.tree_relationships
        for iid in tree.get_children():
            tree.delete(iid)

        if not invoice or not getattr(invoice, "_relationships", None):
            return

        tokens = getattr(invoice, "_tokens", [])
        for sid, relationship in enumerate(invoice._relationships):
            tag_name: relationship_types = relationship.type

            if relationship.span_a is None or relationship.span_b is None:
                continue

            span_a: GSpan = relationship.span_a
            span_b: GSpan = relationship.span_b

            span_a_text: str = AppData.invoice._get_span_text(span_a)
            span_b_text: str = AppData.invoice._get_span_text(span_b)

            parent = tree.insert("", "end", values=(tag_name.text, sid, span_b_text), tags="RELATIONSHIP")

            tree.insert(parent, "end", values=("POTOMEK A", span_a.id, span_a_text), tags="SPAN")
            tree.insert(parent, "end", values=("POTOMEK B", span_b.id, span_b_text), tags="SPAN")

    # ---------- obsluha kliků ----------

    def _on_middle_press(self, event) -> None:
        if self._on_middle_click:
            self._on_middle_click(
                (event.x_root, event.y_root),
                (event.x, event.y),
                EventSource.ENTITIES_PANEL,
            )
        curItem = event.widget.focus()
        # print(event.widget.item(curItem))

    def _on_right_press(self, event):
        self._focus_item_under_mouse(event)
        curItem = event.widget.focus()
        # if curItem:
        #     print(event.widget.item(curItem))
        if self._on_right_click:
            self._on_right_click(
                (event.x_root, event.y_root),
                (event.x, event.y),
                EventSource.ENTITIES_PANEL,

            )
