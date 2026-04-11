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

class InfoC(InvoiceComponent):
   
    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        # Šířka bloku - tentokrát ho uděláme širší, aby mohl být dominantní
        width = mm(85) 

        # 2. Definice polí v řádcích s "vůdcovskými" tečkami nebo čistým zarovnáním
        fields = [
            ("variable_symbol", "Variabilní symbol", SpanTag.VARIABLE_SYMBOL),
            ("issue_date", "Datum vystavení", SpanTag.ISSUE_DATE),
            ("taxable_supply_date", "Datum zdan. plnění", SpanTag.TAXABLE_SUPPLY_DATE),
            ("const_symbol", "Konstantní symbol", SpanTag.CONST_SYMBOL)
        ]

        textRenderer._text(invoice, (x, y), text="Doklad č.", font=textRenderer._f13, fill=MUTED)
        # 1. Číslo faktury s výrazným podtržením
        textRenderer._text(invoice, (x + mm(45), y), text=safe(data.invoice_number), 
                 font=textRenderer._f11b, fill=INK, span_tag=SpanTag.INVOICE_NUMBER)
        y += mm(5)

        for attr, lab, tag in fields:
            val = safe(getattr(data, attr))
            if val:
                # Popisek vlevo
                textRenderer._text(invoice, (x, y), text=lab, font=textRenderer._f13, fill=MUTED)
                # Hodnota vpravo (zarovnaná k fixnímu bodu)
                textRenderer._text(invoice, (x + mm(45), y), text=val, font=textRenderer._f14b, fill=INK, span_tag=tag)
                
                # Jemná tečkovaná linka mezi labelem a hodnotou pro lepší čitelnost
                # (volitelné, simulujeme pomocí malých čárek)
                y += mm(5)

        # 3. Akcent na splatnost - tentokrát pomocí vertikálního odsazení a fontu
        y += mm(2)
        # Nakreslíme malý čtvereček vedle splatnosti jako vizuální odrážku
        d.rectangle([x, y + mm(1), x + mm(1.5), y + mm(2.5)], fill=TMOBILE_PINK)
        
        textRenderer._text(invoice, (x + mm(4), y), text="SPLATNOST DO:", font=textRenderer._f13b, fill=INK)
        textRenderer._text(invoice, (x + mm(45), y), text=safe(data.due_date), 
                 font=textRenderer._f14b, fill=TMOBILE_PINK, span_tag=SpanTag.DUE_DATE)

        # 4. Spodní uzavírací linka
        y += mm(7)
        d.line([(x, y), (x + width, y)], fill=LINE_MID, width=1)

        return y + mm(5)  