from copy import copy
from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import fit_line_bounding_box_font, px, mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money

from PIL.ImageFont import truetype, FreeTypeFont

class company_a(invoice_component):
    



    @abstractmethod
    def draw(inv:DInvoice, d:ImageDraw, x:int, y:int, **kwargs):
        
        supplier:bool = kwargs.get("supplier", True)
        width = kwargs.get("width", None)
        height = kwargs.get("height", None)

        if not width:
            width = mm(85)

        if not height:
            height = mm(70)

        scaled_f12b = copy(inv._f12b)
        scaled_f11 = copy(inv._f11)
        scaled_f10 = copy(inv._f10)

        space: int = 0
        number_of_informations = 6

        values = inv.supplier if supplier else inv.customer

        if not width or not height:
            space = mm(5)

        things_to_be_written = [
            f"IČ: {safe(values.register_id)}",
            f"daňové identifikační číslo: {safe(values.tax_id)}",
            safe(values.name),
            f"adresa: {safe(values.address)}"
        ]

        max_font_size = inv._f16b.size

        for thing in things_to_be_written:
            _, font_size = fit_line_bounding_box_font(thing, width, inv._f12.path, default_font_size=30)
            max_font_size = min(max_font_size, font_size)


        if width and height:
            space = min(mm(5), (float)(height)/number_of_informations)
            font_scale:float = width/mm(50)
            font_scale = min(font_scale, 1)

            scaled_f12b = truetype(inv._f12b.path, max_font_size)
            scaled_f11 = truetype(inv._f11.path, max_font_size - 1)
            scaled_f10 = truetype(inv._f10.path, max_font_size - 2)



        inv._text(d, (x, y), text="Dodavatel:" if supplier else "Zákazník:", font=scaled_f12b, fill=INK)

        y += space + mm(1)
        inv._text(d, (x, y), label="", text=safe(values.name), font=scaled_f11, fill=INK)
        y += space
        inv._text(d, (x, y), label="adresa:", text=safe(values.address), font=scaled_f10, fill=INK)
        y += space
        
        if random.random() > 0.1:
            if(supplier):
                inv._text(d, (x, y), label="IČ:", text=safe(values.register_id), font=scaled_f10, fill=INK, span_tag=span_tags.SUPPLIER_REGISTER_ID)
                y += space
            else:
                inv._text(d, (x, y), label="IČ:", text=safe(values.register_id), font=scaled_f10, fill=INK, span_tag=span_tags.CUSTOMER_REGISTER_ID)
                y += space


        if random.random() > 0.1:
            if(supplier):
                inv._text(d, (x, y), label="DIČ:", text=safe(values.tax_id), font=scaled_f10, fill=INK, span_tag=span_tags.SUPPLIER_TAX_ID)
            else:
                inv._text(d, (x, y), label="DIČ:", text=safe(values.tax_id), font=scaled_f10, fill=INK, span_tag=span_tags.CUSTOMER_TAX_ID)

        return y + space

