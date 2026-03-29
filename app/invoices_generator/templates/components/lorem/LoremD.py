from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer

from invoices_generator.core.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect, get_rand_date
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money



class LoremD(InvoiceComponent):

    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        max_w = kwargs.get("width", mm(85))
        start_y = y

        # 1. NADPIS BLOKU
        textRenderer._text(invoice, d, (x, y), text="DŮLEŽITÉ INFORMACE A ZÁRUKA", font=textRenderer._f8b, fill=INK)
        y += mm(5)


        # 2. GENERAČNÍ VATA S DATY
        # Tyto věty obsahují náhodná data, aby model musel filtrovat šum
        data_phrases = [
            f"Záruční lhůta na vybrané komponenty počíná běžet dnem {get_rand_date()}.",
            f"Poslední revize obchodních podmínek proběhla dne {get_rand_date()}.",
            f"Akční nabídka věrnostních bodů je platná pouze do {get_rand_date()}.",
            f"Předpokládaný termín naskladnění dalších položek je {get_rand_date()}.",
            f"Servisní prohlídka zařízení byla stanovena na termín: {get_rand_date()}.",
            f"Tento doklad byl archivován v systému dne {get_rand_date()} v 14:20.",
            f"Licenční ujednání nabývá účinnosti nejdříve od {get_rand_date()}."
        ]

        random.shuffle(data_phrases)
        
        # Vykreslíme 3 náhodné věty s word-wrapem
        for phrase in data_phrases[:3]:
            words = phrase.split(' ')
            line = "• "
            for word in words:
                if text_width(line + word, textRenderer._f8) < (max_w - mm(5)):
                    line += word + " "
                else:
                    textRenderer._text(invoice, d, (x, y), text=line, font=textRenderer._f8, fill=MUTED)
                    y += mm(3.5)
                    line = "  " + word + " "
            textRenderer._text(invoice, d, (x, y), text=line, font=textRenderer._f8, fill=MUTED)
            y += mm(4.5)

        y += mm(2)

        # 3. VIZUÁLNÍ PRVEK: Razítko "EXPEDOVÁNO"
        # Čtvercové razítko s náhodným datem uvnitř
        stamp_x = x + max_w - mm(35)
        stamp_y = start_y + mm(2)
        
        d.rectangle([stamp_x, stamp_y, stamp_x + mm(30), stamp_y + mm(12)], outline=(50, 150, 50), width=2)
        textRenderer._text(invoice, d, (stamp_x + mm(4), stamp_y + mm(2)), text="EXPEDOVÁNO", font=textRenderer._f8b, fill=(50, 150, 50))
        textRenderer._text(invoice,d, (stamp_x + mm(7), stamp_y + mm(7)), text=get_rand_date(), font=textRenderer._f8, fill=(50, 150, 50))

        return max(y, stamp_y + mm(15)) + mm(5)
