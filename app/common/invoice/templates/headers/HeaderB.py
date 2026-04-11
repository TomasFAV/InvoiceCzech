from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer

from common.data.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from common.utils.utilities import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from common.utils.consts import _A4_W_PX, INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from common.utils.utilities import safe, fmt_money


class HeaderB(InvoiceComponent):
    
    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)

        page_width = _A4_W_PX - (2 * x)
        start_y = y

        # 1. Grafický prvek v rohu (diagonální linky pro moderní vzhled)
        for i in range(0, 20, 4):
            d.line([(x + page_width - mm(20) + mm(i), start_y), 
                    (x + page_width + mm(i), start_y + mm(20))], 
                   fill=SUBTLE_BG, width=1)

        # 2. Hlavní název firmy (vlevo)
        textRenderer._text(invoice, (x, y), text=safe(data.supplier.name).upper(), font=textRenderer._f12b, fill=INK)
        y += mm(6)
        textRenderer._text(invoice, (x, y), text="SPECIALIZOVANÝ MALOOBCHOD A SERVIS", font=textRenderer._f10, fill=TMOBILE_PINK)
        
        # 3. Horní horizontální předěl
        y += mm(4)
        d.line([(x, y), (x + page_width, y)], fill=LINE_MID, width=1)
        y += mm(2)

        # 4. Blok "na tvrdo" informací (vlevo pod čarou)
        # Právní vata
        legal_text = "Zápis v OR: Městský soud v Praze, oddíl C, vložka 123456"
        textRenderer._text(invoice, (x, y), text=legal_text, font=textRenderer._f10, fill=MUTED)
        
        # 5. Pravý blok s ID schránky a Provozovnou (na tvrdo)
        r_align = -2*x + page_width
        
        # Horní pozice pro pravý blok (zarovnáno s legal_text)
        textRenderer._text(invoice, (r_align, y), text="ID datové schránky: 8t5sa2q", font=textRenderer._f10, fill=MUTED)
        y += mm(3.5)
        textRenderer._text(invoice, (r_align, y), text="Provozovna: Průmyslová 14, 102 00 Praha 10", font=textRenderer._f10, fill=MUTED)
        
        # 6. "Nedůležité" metadata (vlevo)
        y -= mm(0) # mírná korekce výšky
        textRenderer._text(invoice, (x, y), text="Certifikace: ISO 9001:2015 Management kvality", font=textRenderer._f10, fill=MUTED)

        # 7. Finální podtržení, které uzavírá celou hlavičku
        y += mm(6)
        d.line([(x, y), (x + page_width, y)], fill=LINE_STRONG, width=2)
        
        # Vrácení pozice pro zbytek faktury
        return y + mm(10)