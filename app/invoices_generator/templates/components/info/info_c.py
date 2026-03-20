from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money

class info_c(invoice_component):

    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        # Šířka bloku - tentokrát ho uděláme širší, aby mohl být dominantní
        width = mm(85) 

        # 2. Definice polí v řádcích s "vůdcovskými" tečkami nebo čistým zarovnáním
        fields = [
            ("variable_symbol", "Variabilní symbol", span_tags.VARIABLE_SYMBOL),
            ("issue_date", "Datum vystavení", span_tags.ISSUE_DATE),
            ("taxable_supply_date", "Datum zdan. plnění", span_tags.TAXABLE_SUPPLY_DATE),
            ("const_symbol", "Konstantní symbol", span_tags.CONST_SYMBOL)
        ]

        inv._text(d, (x, y), text="Doklad č.", font=inv._f13, fill=MUTED)
        # 1. Číslo faktury s výrazným podtržením
        inv._text(d, (x + mm(45), y), text=safe(inv.invoice_number), 
                 font=inv._f11b, fill=INK, span_tag=span_tags.INVOICE_NUMBER)
        y += mm(5)

        for attr, lab, tag in fields:
            val = safe(getattr(inv, attr))
            if val:
                # Popisek vlevo
                inv._text(d, (x, y), text=lab, font=inv._f13, fill=MUTED)
                # Hodnota vpravo (zarovnaná k fixnímu bodu)
                inv._text(d, (x + mm(45), y), text=val, font=inv._f14b, fill=INK, span_tag=tag)
                
                # Jemná tečkovaná linka mezi labelem a hodnotou pro lepší čitelnost
                # (volitelné, simulujeme pomocí malých čárek)
                y += mm(5)

        # 3. Akcent na splatnost - tentokrát pomocí vertikálního odsazení a fontu
        y += mm(2)
        # Nakreslíme malý čtvereček vedle splatnosti jako vizuální odrážku
        d.rectangle([x, y + mm(1), x + mm(1.5), y + mm(2.5)], fill=TMOBILE_PINK)
        
        inv._text(d, (x + mm(4), y), text="SPLATNOST DO:", font=inv._f13b, fill=INK)
        inv._text(d, (x + mm(45), y), text=safe(inv.due_date), 
                 font=inv._f14b, fill=TMOBILE_PINK, span_tag=span_tags.DUE_DATE)

        # 4. Spodní uzavírací linka
        y += mm(7)
        d.line([(x, y), (x + width, y)], fill=LINE_MID, width=1)

        return y + mm(5)