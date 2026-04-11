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
from common.utils.utilities import safe, fmt_money, get_item_value

class TotalB(InvoiceComponent):
 

    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        # Šířka bloku
        box_w = mm(75)
        box_h = mm(18)
        
        # 1. HLAVNÍ BLOK (Inverzní barva - tmavý podklad)
        # Použijeme barvu INK nebo TMOBILE_PINK pro výrazný efekt
        d.rectangle([x - mm(5), y - mm(2), x + box_w - mm(5), y + box_h], fill=BG)
        
        # 2. POPIS (Malé písmo, kontrastní barva)
        textRenderer._text(invoice, (x, y), text="CELKOVÁ ČÁSTKA K ÚHRADĚ", font=textRenderer._f8b, fill=BG)
        
        y += mm(5)
        
        # 3. ČÁSTKA (Velké, tučné, bílé/kontrastní písmo)
        total_txt = f"{fmt_money(data.calculated_total_price)}"
        
        # Výpočet pozice pro zarovnání doprava v rámci boxu
        # (Pokud tvůj systém nepodporuje _draw_right s barvou, použijeme klasický text)
        textRenderer._text(invoice, (x, y), text=total_txt, end=f"{data.currency.value}", font=textRenderer._f18b, fill=BG, span_tag=SpanTag.TOTAL)
        
        # 4. DOPLNĚK (Např. kurz nebo poznámka pod čarou v rámci boxu)
        textRenderer._text(invoice, (x, y + mm(8)), text="Včetně DPH a všech poplatků", font=textRenderer._f8, fill=SUBTLE_BG)

        return y + mm(5)