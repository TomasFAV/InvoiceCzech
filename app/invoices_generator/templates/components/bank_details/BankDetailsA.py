from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer

from invoices_generator.core.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money

class BankDetailsA(InvoiceComponent):
       

    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
        width = mm(75)

        style = get_random_style()
        draw_styled_rect(d, [x-mm(2), y-mm(2), x+width, y+mm(18)], style)
        
        bank_fields = [
            ("Bankovní spojení", data.bank_account_number, "Číslo účtu", SpanTag.BANK_ACCOUNT_NUMBER),
            ("IBAN", data.IBAN, "IBAN", SpanTag.IBAN),
            ("BIC", data.bank_account.BIC, "BIC", SpanTag.BIC)
        ]
        
        random.shuffle(bank_fields)

        for lab, val, lab, tag in bank_fields:
            if random.random() > 0.1:
                textRenderer._text(invoice, d, (x, y), label=lab, text=safe(val), font=textRenderer._f13, fill=INK, span_tag=tag)
                y += mm(4.5)
        

        return y
