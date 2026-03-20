from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money, get_item_value

from PIL.ImageFont import truetype, FreeTypeFont

class table_a(invoice_component):
    



    @abstractmethod
    def draw(inv:DInvoice, d:ImageDraw, x:int, y:int, **kwargs):
        width: int = kwargs.get("width", None)
        height: int = kwargs.get("height", None)

        config = [("Popis", "description", 0.4),
                  ("Množství", "quantity", 0.1),
                  ("DPH %", "vat_percentage", 0.1),
                  ("J. cena", "ppu", 0.15),
                  ("Celkem", "price_with_vat", 0.25)]

        if not width:
            width = mm(170)

        if not height:
            height = mm(80)

        table_w = width
        random.shuffle(config)

        #plus hlavička
        row_height = min(float(height) / (len(inv.items) + 1), 50) #max 50px
        font_size = row_height * 0.55

        scaled_f10 = truetype(inv._f10.path, font_size)

        col_abs = [int(col[2] * table_w) for col in config]
        x_cols = [x]
        for w in col_abs[:-1]: x_cols.append(x_cols[-1] + w)

        # Záhlaví tabulky
        d.line([(x, y), (x + table_w, y)], fill=LINE_STRONG, width=2)

        for i, col in enumerate(config):
            inv._text(d, (x_cols[i] + width*0.05, y + row_height*0.05), col[0], font=inv._f12b, fill=INK)
        y += row_height

        d.line([(x, y), (x + table_w, y)], fill=LINE, width=1)

        # Položky s Zebra efektem
        for idx, it in enumerate(inv.items):
            if idx % 2 == 0:
                d.rectangle([x, y, x + table_w, y + row_height], fill=(250, 250, 250))
            
            for i, col in enumerate(config):
                val = get_item_value(it, col[1])
                inv._text(d, (x_cols[i] + width*0.05, y + row_height*0.05), val, font=inv._f12, fill=INK)
            
            y += row_height
    

        return y