from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer

from invoices_generator.core.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money


class InfoA(InvoiceComponent):
    
    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)

        textRenderer._text(invoice, d, (x, y), f"{safe(data.invoice_number)}", font=textRenderer._f13b, fill=INK, span_tag=SpanTag.INVOICE_NUMBER,
        label="Číslo faktury")
        y += mm(8)
        
        fields = [
            ("issue_date", "Datum vysvatení:", SpanTag.ISSUE_DATE),
            ("due_date", "Datum splatnosti:", SpanTag.DUE_DATE),
            ("taxable_supply_date", "DUZP:", SpanTag.TAXABLE_SUPPLY_DATE),
            ("variable_symbol", "Variabilní symbol:", SpanTag.VARIABLE_SYMBOL),
            ("const_symbol", "Konstantní symbol:", SpanTag.CONST_SYMBOL)
        ]
       
        random.shuffle(fields)

        for attr, lab, tag in fields:
            if random.random() > 0.15:
                textRenderer._text(invoice, d, (x, y), label=lab, text=safe(getattr(data, attr)), font=textRenderer._f14, fill=INK, span_tag=tag)
                y += mm(5)
        
        return y

