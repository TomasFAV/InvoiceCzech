from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money



class header_c(invoice_component):
    
    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        style = get_random_style()
        
        page_width = inv._A4_W_PX - (2 * x)
        start_y = y
        
        # 1. Horní "Slim" linka - jen estetický začátek
        d.line([(x, y), (x + mm(15), y)], fill=TMOBILE_PINK, width=2)
        y += mm(4)

        # 2. Název firmy - dominantní prvek
        inv._text(d, (x, y), text=safe(inv.supplier.name).upper(), font=inv._f16b, fill=INK)
        
        # Sekce vpravo - Číslo faktury (aby nahoře nebylo prázdno)
        inv._text(d, (-2*x + page_width, y), label="Doklad:", text=f"{safe(inv.invoice_number)}", 
                  font=inv._f12b, fill=INK, span_tag=span_tags.INVOICE_NUMBER)
        
        y += mm(8)

        # 3. Vertikální info blok (Sidebar styl)
        # Nakreslíme svislou linku, u které budou ty "vaty"
        sidebar_x = -2*x + mm(2)
        line_height = mm(17)
        d.line([(x, y), (x, y + line_height)], fill=LINE_MID, width=1)
        
        # Texty v bloku (na tvrdo)
        # Odsadíme text trochu od svislé linky (x + mm(3))
        text_x = x + mm(3)
        current_v_y = y
        
        # Skupina 1: Registrace
        inv._text(d, (text_x, current_v_y), text="REGISTRACE:", font=inv._f10b, fill=MUTED)
        current_v_y += mm(3.5)
        inv._text(d, (text_x, current_v_y), text="Městský soud v Praze, odd. C, vl. 123456", font=inv._f10, fill=INK)
        
        current_v_y += mm(5)
        
        # Skupina 2: Provozovna a Datovka
        inv._text(d, (text_x, current_v_y), text="PROVOZOVNA & KONTAKT:", font=inv._f10b, fill=MUTED)
        current_v_y += mm(3.5)
        inv._text(d, (text_x, current_v_y), 
                 text="Průmyslová 14, Praha | DS: 8t5sa2q | cert. ISO 9001", 
                 font=inv._f10, fill=INK)

        # 4. Grafický prvek - "Razítko" pozadí
        # Jemný text v pozadí vpravo, aby to nevypadalo prázdné
        inv._text(d, (page_width-2*x, y + mm(5)), text="ORIGINAL", font=inv._f16b, fill=SUBTLE_BG)

        # 5. Spodní uzavírací linka hlavičky (přes celou šířku)
        y += line_height
        d.line([(x, y), (x + page_width, y)], fill=LINE_STRONG, width=1)
        
        # Malý čtvereček na křížení linek pro industriální look
        draw_styled_rect(d, (x - 1, y - 1, x + 1, y + 1), style)

        return y