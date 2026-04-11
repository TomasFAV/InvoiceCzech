from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common import Span

from common.data.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from common.utils.utilities import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from common.utils.consts import _A4_W_PX, INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from common.utils.utilities import safe, fmt_money

class BankDetailsB(InvoiceComponent):
    
    
    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        # 1. BEZPEČNÝ VÝPOČET ŠÍŘKY
        # Pokud by max_width vyšlo záporné, nastavíme minimální rozumnou šířku
        avail_width = _A4_W_PX - (2 * x)
        max_width = max(kwargs.get("width", avail_width), mm(50))
        is_narrow = max_width < mm(120)  # Detekce "úzkého" režimu
        
        padding = mm(3)
        # Výška boxu se adaptuje – v úzkém režimu potřebujeme víc místa na výšku
        box_height = mm(32) if is_narrow else mm(18)
        
        # 1. Podkladový box
        d.rectangle([x, y, x + max_width, y + box_height], fill=SUBTLE_BG, outline=LINE_MID)
        d.rectangle([x, y, x + mm(1.5), y + box_height], fill=INK)
        
        curr_x = x + mm(5)
        curr_y = y + mm(3)

        # --- SEKCE A: Tuzemský účet ---
        textRenderer._text(invoice, (curr_x, curr_y), text="ČÍSLO ÚČTU", font=textRenderer._f10b, fill=MUTED)
        textRenderer._text(invoice, (curr_x, curr_y + mm(4)), 
                 text=safe(data.bank_account_number), 
                 font=textRenderer._f13b if not is_narrow else textRenderer._f14b, # Smrsknutí fontu
                 fill=INK, span_tag=SpanTag.BANK_ACCOUNT_NUMBER)
        
        if not is_narrow:
            textRenderer._text(invoice, (curr_x, curr_y + mm(9)), text="Banka: Centrální Komerční Banka, a.s.", font=textRenderer._f12, fill=MUTED)
            curr_x += mm(60) # Posun doprava v širokém režimu
        else:
            curr_y += mm(12) # Posun dolů v úzkém režimu
            # V úzkém režimu nakreslíme horizontální dělící linku místo svislé
            d.line([(x + mm(5), curr_y - mm(2)), (x + max_width - mm(5), curr_y - mm(2))], fill=LINE_MID, width=1)

        # --- SEKCE B: Mezinárodní údaje ---
        # V úzkém režimu píšeme pod sebe
        textRenderer._text(invoice, (curr_x, curr_y), text="IBAN / BIC", font=textRenderer._f12b, fill=MUTED, must_have_same_width=True)
        
        iban_val = safe(data.IBAN)
        # Pokud je IBAN moc dlouhý a jsme v úzkém režimu, můžeme ho zkrátit nebo zmenšit
        textRenderer._text(invoice, (curr_x, curr_y + mm(4)), text=iban_val, 
                 font=textRenderer._f13b if not is_narrow else textRenderer._f14b, fill=INK, span_tag=SpanTag.IBAN)
        
        if not is_narrow:
            textRenderer._text(invoice, (curr_x, curr_y + mm(9)), 
                     text="Měna: CZK | Clearing: DOMESTIC", font=textRenderer._f12, fill=MUTED)
        else:
            # V úzkém režimu dáme BIC vedle IBANu nebo pod něj
            textRenderer._text(invoice, (curr_x, curr_y + mm(8)), label="BIC: ", text=f"{safe(data.bank_account.BIC)}", font=textRenderer._f12b, fill=INK, span_tag=SpanTag.BIC)

        return y + box_height + mm(5)
