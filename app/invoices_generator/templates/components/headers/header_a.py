from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money


class header_a(invoice_component):
    


    def __init__(self):
        pass


    @abstractmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        # Šířka stránky (orientačně pro linku)
        page_width = inv._A4_W_PX - (2 * x)
        start_y = y

        # 1. Vykreslení Loga (pokud existuje)
        # Předpokládáme, že logo je v inv.supplier.logo_path nebo podobně
        logo_size = mm(15)
        # Zde by byla logika pro d.bitmap nebo d.image, pro teď simulujeme boxem/textem
        inv._text(d, (x, y), text="LOGO", font=inv._f16b, fill=INK)
        
        # 2. Název dokladu a doplňkové info (vpravo)
        r_align =  page_width - 2*x
        inv._text(d, (r_align, y), text="FAKTURA - DAŇOVÝ DOKLAD", font=inv._f14b, fill=INK)
        y += mm(6)
        inv._text(d, (r_align, y), label="Číslo dokladu: ", text=f"{safe(inv.invoice_number)}",
                   font=inv._f10, fill=INK, span_tag=span_tags.INVOICE_NUMBER)
        
        # Posuneme y dolů pod logo
        y = start_y + logo_size
        
        # 3. Estetické podtržení (linka přes celou šířku)
        # Používáme LINE_MID pro jemnější vzhled
        d.line([(x, y), (x + page_width, y)], fill=LINE_MID, width=1)
        
        y += mm(2)
        
        # 4. "Nedůležité" drobné info pod čarou (např. web, email, strana)
        small_info = f"Web: www.web.cz  |  Email: napistemi@gmail.cz"
        inv._text(d, (x, y), text=small_info, font=inv._f8, fill=INK)
        
        return y
    

