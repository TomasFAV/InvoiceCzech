from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core import span
from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money

class bank_details_b(invoice_component):
    



    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        # 1. BEZPEČNÝ VÝPOČET ŠÍŘKY
        # Pokud by max_width vyšlo záporné, nastavíme minimální rozumnou šířku
        avail_width = inv._A4_W_PX - (2 * x)
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
        inv._text(d, (curr_x, curr_y), text="ČÍSLO ÚČTU", font=inv._f10b, fill=MUTED)
        inv._text(d, (curr_x, curr_y + mm(4)), 
                 text=safe(inv.bank_account_number), 
                 font=inv._f13b if not is_narrow else inv._f14b, # Smrsknutí fontu
                 fill=INK, span_tag=span_tags.BANK_ACCOUNT_NUMBER)
        
        if not is_narrow:
            inv._text(d, (curr_x, curr_y + mm(9)), text="Banka: Centrální Komerční Banka, a.s.", font=inv._f12, fill=MUTED)
            curr_x += mm(60) # Posun doprava v širokém režimu
        else:
            curr_y += mm(12) # Posun dolů v úzkém režimu
            # V úzkém režimu nakreslíme horizontální dělící linku místo svislé
            d.line([(x + mm(5), curr_y - mm(2)), (x + max_width - mm(5), curr_y - mm(2))], fill=LINE_MID, width=1)

        # --- SEKCE B: Mezinárodní údaje ---
        # V úzkém režimu píšeme pod sebe
        inv._text(d, (curr_x, curr_y), text="IBAN / BIC", font=inv._f12b, fill=MUTED, must_have_same_width=True)
        
        iban_val = safe(inv.IBAN)
        # Pokud je IBAN moc dlouhý a jsme v úzkém režimu, můžeme ho zkrátit nebo zmenšit
        inv._text(d, (curr_x, curr_y + mm(4)), text=iban_val, 
                 font=inv._f13b if not is_narrow else inv._f14b, fill=INK, span_tag=span_tags.IBAN)
        
        if not is_narrow:
            inv._text(d, (curr_x, curr_y + mm(9)), 
                     text="Měna: CZK | Clearing: DOMESTIC", font=inv._f12, fill=MUTED)
        else:
            # V úzkém režimu dáme BIC vedle IBANu nebo pod něj
            inv._text(d, (curr_x, curr_y + mm(8)), label="BIC: ", text=f"{safe(inv.bank_account.BIC)}", font=inv._f12b, fill=INK, span_tag=span_tags.BIC)

        return y + box_height + mm(5)
    

