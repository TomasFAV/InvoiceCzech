from copy import copy
from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.Span import Span

from common.data.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from common.utils.utilities import fit_line_bounding_box_font, mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from common.utils.consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from common.utils.utilities import safe, fmt_money

from PIL.ImageFont import truetype, FreeTypeFont

class CompanyC(InvoiceComponent):

    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        
        supplier: bool = kwargs.get("supplier", True)
        width: int = kwargs.get("width", None)
        height: int = kwargs.get("height", None)

        if not width:
            width = mm(85)

        if not height:
            height = mm(70)

        values = data.supplier if supplier else data.customer

        space = mm(4)

        # Najdeme max velikost fontu, aby se vešly nejdelší řádky
        things_to_be_written = [
            safe(values.name).upper(),
            f"IČ: {safe(values.register_id)}",
            f"daňové identifikační číslo: {safe(values.tax_id)}",
            f"{safe(values.address)}",
            f"Telefonní spojení: {safe(values.phone)}",
        ]   

        max_font_size = textRenderer._f16b.size
        for thing in things_to_be_written:
            _, font_size = fit_line_bounding_box_font(
                thing,
                width,
                textRenderer._f12.path,
                default_font_size=25,
                min_font_size=5,
            )
            max_font_size = min(max_font_size, font_size)

        
        scaled_f8 = copy(textRenderer._f8)
        scaled_f8b = copy(textRenderer._f8b)
        scaled_f9 = copy(textRenderer._f9)
        scaled_f10 = copy(textRenderer._f10)
        scaled_f10b = copy(textRenderer._f10b)
        scaled_f11b = copy(textRenderer._f11b)

        if width and height:
            y_scale = (float)(height)/mm(35)
            y_scale = max(min(y_scale, 1),0.5)

            x_scale:float = (float)(width)/mm(40)
            x_scale = min(x_scale, 2)

            font_scale = min(x_scale, y_scale)

            number_of_lines_target = 8
            space = min(float(height) / number_of_lines_target, float(mm(5)))

            scaled_f8 = truetype(textRenderer._f8.path, max_font_size-4)
            scaled_f8b = truetype(textRenderer._f8b.path, max_font_size-3)
            scaled_f9 = truetype(textRenderer._f9.path, max_font_size-2)
            scaled_f10 = truetype(textRenderer._f15.path, max_font_size-1)
            scaled_f10b = truetype(textRenderer._f15b.path, max_font_size)

        block_start_y = y

        # 1. Malý "Badge" (štítek) nad jménem
        # Místo boxu jen podbarvený text v malém rámečku
        label_text = "DODAVATEL" if supplier else "ODBĚRATEL"
        label_w = text_width(label_text, scaled_f8b) + mm(4)
        
        style = get_random_style()

        # Malé zakulacené pozadí pro label
        draw_styled_rect(d, (x, y, x + label_w, y + mm(4)), style)
        textRenderer._text(invoice, (x + mm(2), y + mm(0.5)), text=label_text, font=scaled_f8b, fill=MUTED)
        
        y += space * 1.2

        # 2. Jméno firmy s výrazným "trackingem" (prokládáním)
        # Použijeme tučné písmo, ale menší velikost pro elegantnější vzhled
        company_name = safe(values.name).upper()
        textRenderer._text(invoice, (x, y), text=company_name, font=scaled_f10b, fill=INK)
        
        y += space * 1.1
        adress_start_y = y
        adress_end_x = x
        # 3. Adresa rozdělená na řádky (pokud obsahuje čárku, rozdělíme ji)
        # To vytvoří hezčí blok textu
        addr_parts = safe(values.address).split(',')
        for part in addr_parts:
            adress_end_x = max(textRenderer._text(invoice, (x, y), text=part.strip(), font=scaled_f8, fill=INK)[0], adress_end_x)
            y += space

        y += 0.1 * space

        #hodi ic a dic vedle, kdyz se nevejde pod
        if height is not None and y + space >  block_start_y +  height:
                y = adress_start_y
                x = adress_end_x + mm(2)

        if (supplier):
            textRenderer._text(invoice, (x, y), label="IČ", text=safe(values.register_id), font=scaled_f9, fill=MUTED,
                      span_tag=SpanTag.SUPPLIER_REGISTER_ID)
            y += space
            textRenderer._text(invoice, (x, y), label="DIČ", text=safe(values.tax_id), font=scaled_f9, fill=MUTED,
                      span_tag=SpanTag.SUPPLIER_TAX_ID)
            y += space
        else:
            textRenderer._text(invoice, (x, y), label="IČ", text=safe(values.register_id), font=scaled_f9, fill=MUTED,
                      span_tag=SpanTag.CUSTOMER_REGISTER_ID)
            y += space 
            textRenderer._text(invoice, (x, y), label="DIČ", text=safe(values.tax_id), font=scaled_f9, fill=MUTED,
                      span_tag=SpanTag.CUSTOMER_TAX_ID)
            y += space


        return y + mm(5)