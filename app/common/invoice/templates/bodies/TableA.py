from PIL.ImageDraw import ImageDraw
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.data.InvoiceComponent import InvoiceComponent
from common.utils.utilities import mm
from common.utils.consts import INK, LINE, LINE_STRONG
from common.utils.utilities import get_item_value

from PIL.ImageFont import truetype

class TableA(InvoiceComponent):
    
    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)
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
        row_height = min(float(height) / (len(data.items) + 1), 50) #max 50px
        font_size = row_height * 0.55

        scaled_f10 = truetype(textRenderer._f10.path, font_size)

        col_abs = [int(col[2] * table_w) for col in config]
        x_cols = [x]
        for w in col_abs[:-1]: x_cols.append(x_cols[-1] + w)

        # Záhlaví tabulky
        d.line([(x, y), (x + table_w, y)], fill=LINE_STRONG, width=2)

        for i, col in enumerate(config):
            textRenderer._text(invoice, (x_cols[i] + width*0.05, y + row_height*0.05), col[0], font=textRenderer._f12b, fill=INK)
        y += row_height

        d.line([(x, y), (x + table_w, y)], fill=LINE, width=1)

        # Položky s Zebra efektem
        for idx, it in enumerate(data.items):
            if idx % 2 == 0:
                d.rectangle([x, y, x + table_w, y + row_height], fill=(250, 250, 250))
            
            for i, col in enumerate(config):
                val = get_item_value(it, col[1])
                textRenderer._text(invoice, (x_cols[i] + width*0.05, y + row_height*0.05), val, font=textRenderer._f12, fill=INK)
            
            y += row_height
    

        return y