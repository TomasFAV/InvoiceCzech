from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money


class info_b(invoice_component):

    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        width = mm(85)  # Fixní šířka bloku (půlka stránky)
        padding = mm(4)
        
        style = get_random_style()
        # 1. Pozadí bloku s jemným zaoblením (použijeme BOX_BG nebo SUBTLE_BG)
        draw_styled_rect(d, (x, y, x + width, y + mm(45)), style)
        
        # Horní dekorativní linka pro "vypíchnutí" bloku
        d.rectangle([x, y, x + width, y + mm(1)], fill=TMOBILE_PINK)
        
        y_start = y + mm(5)
        curr_y = y_start

        # 2. Číslo faktury jako nadpis bloku
        inv._text(d, (x + padding, curr_y), label="Doklad č.:", 
                 text=safe(inv.invoice_number), font=inv._f16b, fill=INK, 
                 span_tag=span_tags.INVOICE_NUMBER)
        
        curr_y += mm(8)
        
        # 3. Definice polí
        fields = [
            ("issue_date", "Vystaveno:", span_tags.ISSUE_DATE),
            ("taxable_supply_date", "DUZP:", span_tags.TAXABLE_SUPPLY_DATE),
            ("variable_symbol", "Variabilní s.:", span_tags.VARIABLE_SYMBOL),
            ("const_symbol", "Konstantní s.:", span_tags.CONST_SYMBOL)
        ]
        
        # 4. Vykreslení polí ve dvou sloupcích (grid)
        # Tím ušetříme vertikální místo
        col_width = (width - 2 * padding) / 2
        
        for i, (attr, lab, tag) in enumerate(fields):
            # Výpočet pozice pro 2 sloupce
            col = i % 2
            row = i // 2
            
            field_x = x + padding + (col * col_width)
            field_y = curr_y + (row * mm(7))
            
            val = safe(getattr(inv, attr))
            if val:
                # Menší popisek (label) nad hodnotou nebo vedle ní
                inv._text(d, (field_x, field_y), text=lab, font=inv._f12, fill=MUTED)
                inv._text(d, (field_x, field_y + mm(3.5)), text=val, font=inv._f14b, fill=INK, span_tag=tag)

        # 5. Zvýrazněné datum splatnosti (červené/výrazné) dole
        curr_y += mm(16)
        d.line([(x + padding, curr_y), (x + width - padding, curr_y)], fill=LINE_MID, width=1)
        curr_y += mm(2)
        
        inv._text(d, (x + padding, curr_y), text="Datum splatnosti:", font=inv._f14, fill=INK)
        inv._text(d, (x + width - 4*padding, curr_y), text=safe(inv.due_date), 
                 font=inv._f14b, fill=TMOBILE_PINK, span_tag=span_tags.DUE_DATE)

        return curr_y + mm(8)