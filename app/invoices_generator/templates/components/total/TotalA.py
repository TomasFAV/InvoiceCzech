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
from invoices_generator.utility.utils import safe, fmt_money, get_item_value


class TotalA(InvoiceComponent):
        
    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        
        style = get_random_style()
        draw_styled_rect(d, [x-mm(5), y-mm(3), x+mm(75), y+mm(15)], style)
        
        textRenderer._text(invoice, d, (x, y), text="Celkem k úhrade:", font=textRenderer._f11b, fill=INK)
        y += mm(6)
        total_txt = f"{fmt_money(data.calculated_total_price)}"
        textRenderer._text(invoice, d, (x, y), text=total_txt, end=f"{data.currency.value}", font=textRenderer._f16b, fill=INK, span_tag=SpanTag.TOTAL) 
    
        return y + mm(5)
