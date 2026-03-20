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

class bank_details_c(invoice_component):

    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        # Dynamický výpočet šířky
        avail_width = inv._A4_W_PX - (2 * x)
        width = kwargs.get("width", avail_width)
        
        # Detekce úzkého režimu (pod 100 mm)
        is_compact = width < mm(100)
        
        # Výška se přizpůsobí režimu
        box_h = mm(30) if is_compact else mm(16)
        
        # 1. Podklad s levým barevným akcentem (místo rámečku)
        d.rectangle([x, y, x + width, y + box_h], fill=(252, 252, 252))
        d.rectangle([x, y, x + mm(1), y + box_h], fill=TMOBILE_PINK)
        d.line([(x, y), (x + width, y)], fill=LINE_MID, width=1)

        curr_x = x + mm(4)
        curr_y = y + mm(3)

        if is_compact:
            # --- ÚZKÝ REŽIM (70 mm) ---
            # Banka
            inv._text(d, (curr_x, curr_y), text="BANKA", font=inv._f12b, fill=MUTED)
            inv._text(d, (curr_x + mm(30), curr_y), text="Centrální Komerční Banka", font=inv._f12, fill=INK)
            
            # Číslo účtu
            curr_y += mm(6)
            inv._text(d, (curr_x, curr_y), text="ÚČET", font=inv._f12b, fill=MUTED)
            inv._text(d, (curr_x + mm(30), curr_y - mm(0.5)), text=safe(inv.bank_account_number), 
                     font=inv._f14b, fill=INK, span_tag=span_tags.BANK_ACCOUNT_NUMBER)
            
            # IBAN
            curr_y += mm(7)
            inv._text(d, (curr_x, curr_y), text="IBAN", font=inv._f12b, fill=MUTED)
            inv._text(d, (curr_x + mm(30), curr_y), text=safe(inv.IBAN), 
                     font=inv._f12b, fill=INK, span_tag=span_tags.IBAN)
            
            # BIC
            curr_y += mm(5)
            inv._text(d, (curr_x, curr_y), text="BIC", font=inv._f12b, fill=MUTED)
            inv._text(d, (curr_x + mm(30), curr_y), text=safe(inv.bank_account.BIC), 
                     font=inv._f12, fill=INK, span_tag=span_tags.BIC)
        else:
            # --- ŠIROKÝ REŽIM (Full width) ---
            # Tři sloupce vedle sebe
            col_w = width / 3
            
            # Col 1: Banka
            inv._text(d, (curr_x, curr_y), text="BANKOVNÍ SPOJENÍ", font=inv._f12b, fill=MUTED)
            inv._text(d, (curr_x, curr_y + mm(5)), text="Centrální Komerční Banka", font=inv._f13, fill=INK)
            
            # Col 2: Účet
            inv._text(d, (x + col_w, curr_y), text="ČÍSLO ÚČTU", font=inv._f12b, fill=MUTED)
            inv._text(d, (x + col_w, curr_y + mm(4.5)), text=safe(inv.bank_account_number), 
                     font=inv._f13b, fill=INK, span_tag=span_tags.BANK_ACCOUNT_NUMBER)
            
            # Col 3: IBAN/BIC
            inv._text(d, (x + 2*col_w, curr_y), text="IBAN / BIC", font=inv._f12b, fill=MUTED, must_have_same_width=True)
            inv._text(d, (x + 2*col_w, curr_y + mm(5)), text=f"{safe(inv.IBAN)}", font=inv._f12b, fill=INK, span_tag=span_tags.IBAN)

        return y + box_h + mm(5)

