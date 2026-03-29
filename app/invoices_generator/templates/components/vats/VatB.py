from PIL.ImageDraw import ImageDraw
from PIL.ImageFont import truetype

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer

from invoices_generator.core.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from invoices_generator.utility.utils import fmt_money, mm
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE_MID, SUBTLE_BG


class VatB(InvoiceComponent):

    @staticmethod
    def render(textRenderer: TextRenderer, data: InvoiceData, invoice: Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)

        width = kwargs.get("width")
        height = kwargs.get("height")

        if not width or not height:
            return VatB.draw_normal(textRenderer, data, invoice, d, x, y, **kwargs)
        return VatB.draw_scaled(textRenderer, data, invoice, d, x, y, **kwargs)

    @staticmethod
    def _clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    @staticmethod
    def draw_scaled(textRenderer: TextRenderer, data: InvoiceData, invoice: Invoice, d: ImageDraw, x: int, y: int, **kwargs):
        width: int = kwargs["width"]
        height: int = kwargs["height"]

        rows = max(1, len(data.vat))

        pad_x = width * 0.02
        header_h = height * 0.22
        body_h = max(0, height - header_h)
        row_h = body_h / rows
        row_h = min(row_h, 75)

        base_path = getattr(textRenderer._f8, "path", None)
        size = int(VatB._clamp(row_h * 0.55, 6, 28))
        font = truetype(base_path, size) if base_path else textRenderer._f8

        col1 = x + pad_x
        col2 = x + width * 0.33
        col3 = x + width * 0.78

        # Hlavička
        d.rectangle([x, y, x + width, y + header_h], fill=SUBTLE_BG)

        ty = y + header_h * 0.18
        textRenderer._text(invoice, d, (col1, ty), text="Sazba", font=font, fill=MUTED)
        textRenderer._text(invoice, d, (col2, ty), text="Základ daně", font=font, fill=MUTED)
        textRenderer._text(invoice, d, (col3, ty), text="Daň", font=font, fill=MUTED)

        cy = y + header_h
        for v in data.vat:
            ly = cy + size
            d.line([(x + pad_x, ly), (x + width - pad_x, ly)], fill=LINE_MID, width=1)

            textRenderer._text(
                invoice, d, (col1, cy),
                text=f"{v.vat_percentage}",
                end="%",
                font=font,
                fill=INK,
                span_tag=SpanTag.O
            )
            textRenderer._text(
                invoice, d, (col2, cy),
                text=fmt_money(v.vat_base),
                font=font,
                fill=INK,
                span_tag=SpanTag.O
            )
            textRenderer._text(
                invoice, d, (col3, cy),
                text=fmt_money(v.vat),
                font=font,
                fill=INK,
                span_tag=SpanTag.O
            )

            cy += row_h

        return y + height

    @staticmethod
    def draw_normal(textRenderer: TextRenderer, data: InvoiceData, invoice: Invoice, d: ImageDraw, x: int, y: int, **kwargs):
        width = kwargs.get("width") or mm(85)

        d.rectangle([x, y, x + width, y + mm(6)], fill=SUBTLE_BG)

        col_sazba = x + mm(2)
        col_zaklad = x + mm(25)
        col_dan = x + mm(65)

        textRenderer._text(invoice, d, (col_sazba, y + mm(1)), text="Sazba", font=textRenderer._f8b, fill=MUTED)
        textRenderer._text(invoice, d, (col_zaklad, y + mm(1)), text="Základ daně", font=textRenderer._f8b, fill=MUTED)
        textRenderer._text(invoice, d, (col_dan, y + mm(1)), text="Daň", font=textRenderer._f8b, fill=MUTED)

        y += mm(7)

        for v in data.vat:
            d.line([(x + mm(2), y + mm(5)), (x + width - mm(2), y + mm(5))], fill=LINE_MID, width=1)

            textRenderer._text(
                invoice, d, (col_sazba, y),
                text=f"{v.vat_percentage}",
                end="%",
                font=textRenderer._f10b,
                fill=INK,
                span_tag=SpanTag.O
            )
            textRenderer._text(
                invoice, d, (col_zaklad, y),
                text=fmt_money(v.vat_base),
                font=textRenderer._f10,
                fill=INK,
                span_tag=SpanTag.O
            )
            textRenderer._text(
                invoice, d, (col_dan, y),
                text=fmt_money(v.vat),
                font=textRenderer._f10b,
                fill=INK,
                span_tag=SpanTag.O
            )

            y += mm(6)

        return y + mm(2)