from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money

class bank_details_a(invoice_component):
    



    @abstractmethod
    def draw(inv:DInvoice, d:ImageDraw, x:int, y:int, **kwargs):
        
        width = mm(75)

        style = get_random_style()
        draw_styled_rect(d, [x-mm(2), y-mm(2), x+width, y+mm(18)], style)
        
        bank_fields = [
            ("Bankovní spojení", inv.bank_account_number, "Číslo účtu", span_tags.BANK_ACCOUNT_NUMBER),
            ("IBAN", inv.IBAN, "IBAN", span_tags.IBAN),
            ("BIC", inv.bank_account.BIC, "BIC", span_tags.BIC)
        ]
        
        random.shuffle(bank_fields)

        for lab, val, lab, tag in bank_fields:
            if random.random() > 0.1:
                inv._text(d, (x, y), label=lab, text=safe(val), font=inv._f13, fill=INK, span_tag=tag)
                y += mm(4.5)
        

        return y
    

