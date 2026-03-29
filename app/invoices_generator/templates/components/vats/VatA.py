from copy import copy
from PIL.ImageDraw import ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer

from invoices_generator.core.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from invoices_generator.utility.utils import mm
from invoices_generator.utility.invoice_consts import INK
from invoices_generator.utility.utils import fmt_money

from PIL.ImageFont import truetype, FreeTypeFont

class VatA(InvoiceComponent):

    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):   
        d: ImageDraw = ImageDraw(invoice.image)

        width: int = kwargs.get("width", None)
        height: int = kwargs.get("height", None)
        
        if not height or not width:
            return VatA.draw_normal(textRenderer, data, invoice, d, x, y, **kwargs)
        else:
            return VatA.draw_scaled(textRenderer, data, invoice, d, x, y, **kwargs)

    def draw_scaled(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, d: ImageDraw, x: int, y: int, **kwargs):
        width: int = kwargs.get("width", None)
        height: int = kwargs.get("height", None)
        scaled_f10 = copy(textRenderer._f10)

        x_start, y_start = x, y

        pad_x = width*0.05
        col1 = x_start + pad_x
        col2 = x_start + width*0.33
        col3 = x_start + width*0.78 


        row_height = min(float(height)/len(data.vat), 50) #50px max
        font_size = row_height * 0.55

        scaled_f10 = truetype(textRenderer._f10.path, font_size)


        for v in data.vat:
            x = x_start

            textRenderer._text(invoice, d, (col1,y), text=v.vat_percentage, label="Sazba ", span_tag=SpanTag.O, font=scaled_f10, fill=INK)
            textRenderer._text(invoice, d, (col2,y), text=fmt_money(v.vat_base), label="Základ ", span_tag=SpanTag.O, font=scaled_f10, fill=INK )
            textRenderer._text(invoice, d, (col3,y), text=fmt_money(v.vat), label="Daň ", span_tag=SpanTag.O, font=scaled_f10, fill=INK )   


            y += row_height
    

        return y

    def draw_normal(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, d: ImageDraw, x: int, y: int, **kwargs):
        y_start = y
        x_start = x

        for v in data.vat:
            x = x_start
            x = mm(2) + textRenderer._text(invoice, d, (x,y), text=v.vat_percentage, label="Sazba ", span_tag=SpanTag.O, font=textRenderer._f10, fill=INK )[0]
            x = mm(2) + textRenderer._text(invoice, d, (x,y), text=fmt_money(v.vat_base), label="Základ ", span_tag=SpanTag.O, font=textRenderer._f10, fill=INK )[0]   
            x = mm(2) + textRenderer._text(invoice, d, (x,y), text=fmt_money(v.vat), label="Daň ", span_tag=SpanTag.O, font=textRenderer._f10, fill=INK )[0]

            y += mm(5)
    

        return y
