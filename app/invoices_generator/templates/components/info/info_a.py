from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money


class info_a(invoice_component):
    


    def __init__(self):
        pass


    @abstractmethod
    def draw(inv:DInvoice, d:ImageDraw, x:int, y:int, **kwargs):
        
        inv._text(d, (x, y), f"{safe(inv.invoice_number)}", font=inv._f13b, fill=INK, span_tag=span_tags.INVOICE_NUMBER,
        label="Číslo faktury")
        y += mm(8)
        
        fields = [
            ("issue_date", "Datum vysvatení:", span_tags.ISSUE_DATE),
            ("due_date", "Datum splatnosti:", span_tags.DUE_DATE),
            ("taxable_supply_date", "DUZP:", span_tags.TAXABLE_SUPPLY_DATE),
            ("variable_symbol", "Variabilní symbol:", span_tags.VARIABLE_SYMBOL),
            ("const_symbol", "Konstantní symbol:", span_tags.CONST_SYMBOL)
        ]
       
        random.shuffle(fields)

        for attr, lab, tag in fields:
            if random.random() > 0.15:
                inv._text(d, (x, y), label=lab, text=safe(getattr(inv, attr)), font=inv._f14, fill=INK, span_tag=tag)
                y += mm(5)
        
        return y

