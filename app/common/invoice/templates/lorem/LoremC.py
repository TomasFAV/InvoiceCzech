from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer

from common.data.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from common.utils.utilities import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from common.utils.consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from common.utils.utilities import safe, fmt_money



class LoremC(InvoiceComponent):

    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        max_w = kwargs.get("width", mm(85))
        start_y = y

        # 1. PODKLADOVÝ PRUH (Subtle background)
        # Vytvoříme jemný vizuální předěl
        d.rectangle([x - mm(2), y, x + max_w, y + mm(15)], fill=SUBTLE_BG)
        
        # 2. LEVÁ ČÁST: Právní informace (ve dvou sloupcích/úzký blok)
        text_x = x + mm(2)
        text_y = y + mm(2)
        
        notice_text = (
            "Doklad je vystaven elektronicky a je platný bez razítka. "
            "Splatnost je 14 dní od vystavení, není-li uvedeno jinak."
        )
        
        # Jednoduchý word-wrap pro úzký sloupec (cca 55mm)
        words = notice_text.split(' ')
        line = ""
        for word in words:
            if text_width(line + word, textRenderer._f8) < mm(55):
                line += word + " "
            else:
                textRenderer._text(invoice, (text_x, text_y), text=line, font=textRenderer._f8, fill=INK)
                text_y += mm(3)
                line = word + " "
        textRenderer._text(invoice, (text_x, text_y), text=line, font=textRenderer._f8, fill=INK)

        # 3. PRAVÁ ČÁST: Digitální podpis / Certifikát
        # Místo boxu na podpis použijeme "stuhový" certifikát
        cert_x = x + max_w - mm(35)
        cert_y = y + mm(2)
        
        # Malá ikonka zámku nebo pečeti (čtvereček s textem)
        d.rectangle([cert_x, cert_y, cert_x + mm(30), cert_y + mm(11)], outline=LINE_STRONG, width=1)
        textRenderer._text(invoice, (cert_x + mm(2), cert_y + mm(2)), text="DIGITALLY SIGNED", font=textRenderer._f8b, fill=INK)
        textRenderer._text(invoice, (cert_x + mm(2), cert_y + mm(6)), text="Verified by Auth-ID", font=textRenderer._f8, fill=MUTED)

        y += mm(18)

        # 4. SPODNÍ LINKA S DROBNÝM PÍSMEM (přes celou šířku)
        fine_print = "Zapsáno v OR vedeném MS v Praze, oddíl C, vložka 998877. Děkujeme za nákup!"
        textRenderer._text(invoice, (x, y), text=fine_print, font=textRenderer._f8, fill=MUTED)

        return y + mm(6)