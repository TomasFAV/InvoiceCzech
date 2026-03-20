from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money, get_item_value


class total_a(invoice_component):
    


    @abstractmethod
    def draw(inv:DInvoice, d:ImageDraw, x:int, y:int, **kwargs):
        
        style = get_random_style()
        draw_styled_rect(d, [x-mm(5), y-mm(3), x+mm(75), y+mm(15)], style)
        
        inv._text(d, (x, y), text="Celkem k úhrade:", font=inv._f11b, fill=INK)
        y += mm(6)
        total_txt = f"{fmt_money(inv.calculated_total_price)}"
        inv._text(d, (x, y), text=total_txt, end=f"{inv.currency.value}", font=inv._f16b, fill=INK, span_tag=span_tags.TOTAL) 
    
        return y + mm(5)

