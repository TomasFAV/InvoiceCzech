from copy import copy
from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer

from common.data.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from common.utils.utilities import fit_line_bounding_box_font, px, mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from common.utils.consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from common.utils.utilities import safe, fmt_money

from PIL.ImageFont import truetype, FreeTypeFont

class CompanyA(InvoiceComponent):
    
    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)

        supplier:bool = kwargs.get("supplier", True)
        width = kwargs.get("width", None)
        height = kwargs.get("height", None)

        if not width:
            width = mm(85)

        if not height:
            height = mm(70)

        scaled_f12b = copy(textRenderer._f12b)
        scaled_f11 = copy(textRenderer._f11)
        scaled_f10 = copy(textRenderer._f10)

        space: int = 0
        number_of_informations = 6

        values = data.supplier if supplier else data.customer

        if not width or not height:
            space = mm(5)

        things_to_be_written = [
            f"IČ: {safe(values.register_id)}",
            f"daňové identifikační číslo: {safe(values.tax_id)}",
            safe(values.name),
            f"adresa: {safe(values.address)}"
        ]

        max_font_size = textRenderer._f16b.size

        for thing in things_to_be_written:
            _, font_size = fit_line_bounding_box_font(thing, width, textRenderer._f12.path, default_font_size=30)
            max_font_size = min(max_font_size, font_size)


        if width and height:
            space = min(mm(5), (float)(height)/number_of_informations)
            font_scale:float = width/mm(50)
            font_scale = min(font_scale, 1)

            scaled_f12b = truetype(textRenderer._f12b.path, max_font_size)
            scaled_f11 = truetype(textRenderer._f11.path, max_font_size - 1)
            scaled_f10 = truetype(textRenderer._f10.path, max_font_size - 2)



        textRenderer._text(invoice, (x, y), text="Dodavatel:" if supplier else "Zákazník:", font=scaled_f12b, fill=INK)

        y += space + mm(1)
        textRenderer._text(invoice, (x, y), label="", text=safe(values.name), font=scaled_f11, fill=INK)
        y += space
        textRenderer._text(invoice, (x, y), label="adresa:", text=safe(values.address), font=scaled_f10, fill=INK)
        y += space
        
        if random.random() > 0.1:
            if(supplier):
                textRenderer._text(invoice, (x, y), label="IČ:", text=safe(values.register_id), font=scaled_f10, fill=INK, span_tag=SpanTag.SUPPLIER_REGISTER_ID)
                y += space
            else:
                textRenderer._text(invoice, (x, y), label="IČ:", text=safe(values.register_id), font=scaled_f10, fill=INK, span_tag=SpanTag.CUSTOMER_REGISTER_ID)
                y += space


        if random.random() > 0.1:
            if(supplier):
                textRenderer._text(invoice, (x, y), label="DIČ:", text=safe(values.tax_id), font=scaled_f10, fill=INK, span_tag=SpanTag.SUPPLIER_TAX_ID)
            else:
                textRenderer._text(invoice, (x, y), label="DIČ:", text=safe(values.tax_id), font=scaled_f10, fill=INK, span_tag=SpanTag.CUSTOMER_TAX_ID)

        return y + space