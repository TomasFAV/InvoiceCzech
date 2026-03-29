from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer

from invoices_generator.core.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import _A4_W_PX, INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money


class HeaderA(InvoiceComponent):
    
    
    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        # Šířka stránky (orientačně pro linku)
        page_width = _A4_W_PX - (2 * x)
        start_y = y

        # 1. Vykreslení Loga (pokud existuje)
        # Předpokládáme, že logo je v inv.supplier.logo_path nebo podobně
        logo_size = mm(15)
        # Zde by byla logika pro d.bitmap nebo d.image, pro teď simulujeme boxem/textem
        textRenderer._text(invoice, d, (x, y), text="LOGO", font=textRenderer._f16b, fill=INK)
        
        # 2. Název dokladu a doplňkové info (vpravo)
        r_align =  page_width - 2*x
        textRenderer._text(invoice, d, (r_align, y), text="FAKTURA - DAŇOVÝ DOKLAD", font=textRenderer._f14b, fill=INK)
        y += mm(6)
        textRenderer._text(invoice, d, (r_align, y), label="Číslo dokladu: ", text=f"{safe(data.invoice_number)}",
                   font=textRenderer._f10, fill=INK, span_tag=SpanTag.INVOICE_NUMBER)
        
        # Posuneme y dolů pod logo
        y = start_y + logo_size
        
        # 3. Estetické podtržení (linka přes celou šířku)
        # Používáme LINE_MID pro jemnější vzhled
        d.line([(x, y), (x + page_width, y)], fill=LINE_MID, width=1)
        
        y += mm(2)
        
        # 4. "Nedůležité" drobné info pod čarou (např. web, email, strana)
        small_info = f"Web: www.web.cz  |  Email: napistemi@gmail.cz"
        textRenderer._text(invoice, d, (x, y), text=small_info, font=textRenderer._f8, fill=INK)
        
        return y
    

