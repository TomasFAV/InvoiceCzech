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

class BankDetailsC(InvoiceComponent):

    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        # Dynamický výpočet šířky
        avail_width = _A4_W_PX - (2 * x)
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
            textRenderer._text(invoice, (curr_x, curr_y), text="BANKA", font=textRenderer._f12b, fill=MUTED)
            textRenderer._text(invoice, (curr_x + mm(30), curr_y), text="Centrální Komerční Banka", font=textRenderer._f12, fill=INK)
            
            # Číslo účtu
            curr_y += mm(6)
            textRenderer._text(invoice, (curr_x, curr_y), text="ÚČET", font=textRenderer._f12b, fill=MUTED)
            textRenderer._text(invoice, (curr_x + mm(30), curr_y - mm(0.5)), text=safe(data.bank_account_number), 
                     font=textRenderer._f14b, fill=INK, span_tag=SpanTag.BANK_ACCOUNT_NUMBER)
            
            # IBAN
            curr_y += mm(7)
            textRenderer._text(invoice, (curr_x, curr_y), text="IBAN", font=textRenderer._f12b, fill=MUTED)
            textRenderer._text(invoice, (curr_x + mm(30), curr_y), text=safe(data.IBAN), 
                     font=textRenderer._f12b, fill=INK, span_tag=SpanTag.IBAN)
            
            # BIC
            curr_y += mm(5)
            textRenderer._text(invoice, (curr_x, curr_y), text="BIC", font=textRenderer._f12b, fill=MUTED)
            textRenderer._text(invoice, (curr_x + mm(30), curr_y), text=safe(data.bank_account.BIC), 
                     font=textRenderer._f12, fill=INK, span_tag=SpanTag.BIC)
        else:
            # --- ŠIROKÝ REŽIM (Full width) ---
            # Tři sloupce vedle sebe
            col_w = width / 3
            
            # Col 1: Banka
            textRenderer._text(invoice, (curr_x, curr_y), text="BANKOVNÍ SPOJENÍ", font=textRenderer._f12b, fill=MUTED)
            textRenderer._text(invoice, (curr_x, curr_y + mm(5)), text="Centrální Komerční Banka", font=textRenderer._f13, fill=INK)
            
            # Col 2: Účet
            textRenderer._text(invoice, (x + col_w, curr_y), text="ČÍSLO ÚČTU", font=textRenderer._f12b, fill=MUTED)
            textRenderer._text(invoice, (x + col_w, curr_y + mm(4.5)), text=safe(data.bank_account_number), 
                     font=textRenderer._f13b, fill=INK, span_tag=SpanTag.BANK_ACCOUNT_NUMBER)
            
            # Col 3: IBAN/BIC
            textRenderer._text(invoice, (x + 2*col_w, curr_y), text="IBAN / BIC", font=textRenderer._f12b, fill=MUTED, must_have_same_width=True)
            textRenderer._text(invoice, (x + 2*col_w, curr_y + mm(5)), text=f"{safe(data.IBAN)}", font=textRenderer._f12b, fill=INK, span_tag=SpanTag.IBAN)

        return y + box_h + mm(5)