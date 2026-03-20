from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money, get_item_value

class total_b(invoice_component):

    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        # Šířka bloku
        box_w = mm(75)
        box_h = mm(18)
        
        # 1. HLAVNÍ BLOK (Inverzní barva - tmavý podklad)
        # Použijeme barvu INK nebo TMOBILE_PINK pro výrazný efekt
        d.rectangle([x - mm(5), y - mm(2), x + box_w - mm(5), y + box_h], fill=BG)
        
        # 2. POPIS (Malé písmo, kontrastní barva)
        inv._text(d, (x, y), text="CELKOVÁ ČÁSTKA K ÚHRADĚ", font=inv._f8b, fill=BG)
        
        y += mm(5)
        
        # 3. ČÁSTKA (Velké, tučné, bílé/kontrastní písmo)
        total_txt = f"{fmt_money(inv.calculated_total_price)}"
        
        # Výpočet pozice pro zarovnání doprava v rámci boxu
        # (Pokud tvůj systém nepodporuje _draw_right s barvou, použijeme klasický text)
        inv._text(d, (x, y), text=total_txt, end=f"{inv.currency.value}", font=inv._f18b, fill=BG, span_tag=span_tags.TOTAL)
        
        # 4. DOPLNĚK (Např. kurz nebo poznámka pod čarou v rámci boxu)
        inv._text(d, (x, y + mm(8)), text="Včetně DPH a všech poplatků", font=inv._f8, fill=SUBTLE_BG)

        return y + mm(5)