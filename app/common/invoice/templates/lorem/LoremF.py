from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer

from common.data.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from common.utils.utilities import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect, get_rand_date
from common.utils.consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from common.utils.utilities import safe, fmt_money



class LoremF(InvoiceComponent):

    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        max_w = kwargs.get("width", mm(85))
        start_y = y

        # Konfigurace ikon a barev
        icon_size = mm(3)
        icon_color = TMOBILE_PINK if random.random() > 0.5 else LINE_STRONG
        
        # 1. ZÁSOBNÍK SEKCE (Nadpis + Text)
        sections = [
            ("DOPRAVA A LOGISTIKA", f"Zásilka byla expedována skrze externího dopravce. Sledujte stav pod ID {random.randint(1000,9999)} ze dne {get_rand_date()}."),
            ("PLATEBNÍ PODMÍNKY", f"Uhraďte prosím částku do {get_rand_date()}. Při platbě v měně {data.currency.value} použijte aktuální kurz."),
            ("ZÁKAZNICKÁ PODPORA", f"V případě dotazů nás kontaktujte na help@firma.cz. Poslední aktualizace ticketu: {get_rand_date()}."),
            ("EKOLOGIE", f"Tento dokument byl vytvořen 100% digitálně dne {get_rand_date()} za účelem úspory papíru."),
            ("UPOZORNĚNÍ", f"Neuhrazení faktury do termínu {get_rand_date()} může vést k dočasnému omezení poskytovaných služeb.")
        ]
        
        random.shuffle(sections)
        # Vybereme 3 sekce
        selected = sections[:3]

        for title, text in selected:
            # Kresba "ikony" (barevný čtvereček)
            d.rectangle([x, y + mm(1), x + icon_size, y + mm(1) + icon_size], fill=icon_color)
            
            # Nadpis sekce (vedle ikony)
            textRenderer._text(invoice, (x + icon_size + mm(2), y), text=title, font=textRenderer._f8b, fill=INK)
            y += mm(4.5)
            
            # Word-wrap pro text sekce
            words = text.split(' ')
            line = ""
            for word in words:
                if text_width(line + word, textRenderer._f8) < (max_w - mm(5)):
                    line += word + " "
                else:
                    textRenderer._text(invoice, (x + mm(5), y), text=line.strip(), font=textRenderer._f8, fill=MUTED)
                    y += mm(3.2)
                    line = word + " "
            
            if line:
                textRenderer._text(invoice, (x + mm(5), y), text=line.strip(), font=textRenderer._f8, fill=MUTED)
                y += mm(5) # Mezera mezi sekcemi

        # 2. SPODNÍ DEKORAČNÍ LINKA (často se u těchto moderních boxů používá)
        d.line([(x, y), (x + max_w, y)], fill=SUBTLE_BG, width=1)
        
        y += mm(2)
        # Náhodný systémový kód pro zmatení OCR
        sys_code = f"REF-{random.getrandbits(16)}-{get_rand_date().replace('.', '')}"
        textRenderer._text(invoice, (x, y), text=sys_code, font=textRenderer._f8, fill=MUTED)

        return y + mm(5)