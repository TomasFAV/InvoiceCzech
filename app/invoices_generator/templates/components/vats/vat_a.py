from copy import copy
import math
from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money, get_item_value

from PIL.ImageFont import truetype, FreeTypeFont

class vat_a(invoice_component):


    @abstractmethod
    def draw(inv:DInvoice, d:ImageDraw, x:int, y:int, **kwargs):
        width: int = kwargs.get("width", None)
        height: int = kwargs.get("height", None)
        
        if not height or not width:
            return vat_a.draw_normal(inv, d, x,y, width=width, height=height)
        else:
            return vat_a.draw_scaled(inv, d, x,y, width=width, height=height)

    def draw_scaled(inv:DInvoice, d:ImageDraw, x:int, y:int, **kwargs):
        width: int = kwargs.get("width", None)
        height: int = kwargs.get("height", None)
        scaled_f10 = copy(inv._f10)

        x_start, y_start = x, y

        pad_x = width*0.05
        col1 = x_start + pad_x
        col2 = x_start + width*0.33
        col3 = x_start + width*0.78 


        row_height = min(float(height)/len(inv.vat), 50) #50px max
        font_size = row_height * 0.55

        scaled_f10 = truetype(inv._f10.path, font_size)


        for v in inv.vat:
            x = x_start

            inv._text(d, (col1,y), text=v.vat_percentage, label="Sazba ", span_tag=span_tags.VAT_PERCENTAGE, font=scaled_f10, fill=INK)
            inv._text(d, (col2,y), text=fmt_money(v.vat_base), label="Základ ", span_tag=span_tags.VAT_BASE, font=scaled_f10, fill=INK )
            inv._text(d, (col3,y), text=fmt_money(v.vat), label="Daň ", span_tag=span_tags.VAT_PERCENTAGE, font=scaled_f10, fill=INK )   


            y += row_height
    

        return y

    def draw_normal(inv:DInvoice, d:ImageDraw, x:int, y:int, **kwargs):
        y_start = y
        x_start = x

        for v in inv.vat:
            x = x_start
            x = mm(2) + inv._text(d, (x,y), text=v.vat_percentage, label="Sazba ", span_tag=span_tags.VAT_PERCENTAGE, font=inv._f10, fill=INK )[0]
            x = mm(2) + inv._text(d, (x,y), text=fmt_money(v.vat_base), label="Základ ", span_tag=span_tags.VAT_BASE, font=inv._f10, fill=INK )[0]   
            x = mm(2) + inv._text(d, (x,y), text=fmt_money(v.vat), label="Daň ", span_tag=span_tags.VAT_PERCENTAGE, font=inv._f10, fill=INK )[0]

            y += mm(5)
    

        return y