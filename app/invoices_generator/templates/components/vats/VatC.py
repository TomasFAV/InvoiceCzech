from PIL.ImageDraw import ImageDraw
from PIL.ImageFont import truetype

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer

from invoices_generator.core.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from invoices_generator.utility.utils import mm, fmt_money
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE_MID


class VatC(InvoiceComponent):

    @staticmethod
    def render(textRenderer: TextRenderer, data: InvoiceData, invoice: Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)

        width: int = kwargs.get("width", None)
        height: int = kwargs.get("height", None)

        if not height or not width:
            return VatC.draw_normal(textRenderer, data, invoice, d, x, y, **kwargs)
        return VatC.draw_scaled(textRenderer, data, invoice, d, x, y, **kwargs)

    @staticmethod
    def draw_scaled(textRenderer: TextRenderer, data: InvoiceData, invoice: Invoice, d: ImageDraw, x: int, y: int, **kwargs):
        width = kwargs.get("width", mm(75))
        height = kwargs.get("height", mm(75))

        rows = max(1, len(data.vat))
        row_height = min(float(height) / rows, 75)

        font_size_f8b = max(6, int(row_height * 0.20))
        font_size_f9 = max(6, int(row_height * 0.25))
        font_size_f10b = max(6, int(row_height * 0.30))

        base_f8b_path = getattr(textRenderer._f8b, "path", None)
        base_f9_path = getattr(textRenderer._f9, "path", None)
        base_f10b_path = getattr(textRenderer._f10b, "path", None)

        scaled_f8b = truetype(base_f8b_path, font_size_f8b) if base_f8b_path else textRenderer._f8b
        scaled_f9 = truetype(base_f9_path, font_size_f9) if base_f9_path else textRenderer._f9
        scaled_f10b = truetype(base_f10b_path, font_size_f10b) if base_f10b_path else textRenderer._f10b

        for v in data.vat:
            d.rounded_rectangle(
                [x, y, x + width, y + row_height],
                radius=mm(1),
                fill=(253, 253, 253),
                outline=LINE_MID
            )

            d.rectangle(
                [x, y + row_height * 0.1, x + mm(1), y + row_height - row_height * 0.1],
                fill=INK
            )

            curr_x = x + width * 0.05

            textRenderer._text(
                invoice,
                d,
                (curr_x, y + row_height * 0.1),
                label="DPH",
                text=f"{v.vat_percentage}",
                end="%",
                font=scaled_f8b,
                fill=MUTED,
                span_tag=SpanTag.O
            )

            textRenderer._text(
                invoice,
                d,
                (curr_x, y + row_height * 0.6),
                text="Základ:",
                font=scaled_f8b,
                fill=MUTED
            )
            textRenderer._text(
                invoice,
                d,
                (curr_x + width * 0.1, y + row_height * 0.6),
                text=fmt_money(v.vat_base),
                font=scaled_f9,
                fill=INK,
                span_tag=SpanTag.O
            )

            textRenderer._text_right(
                invoice,
                d,
                x + width - width * 0.1,
                y + row_height * 0.1,
                text="VÝŠE DANĚ",
                font=scaled_f8b,
                fill=MUTED
            )
            textRenderer._text_right(
                invoice,
                d,
                x + width - width * 0.1,
                y + row_height * 0.6,
                text=fmt_money(v.vat),
                font=scaled_f10b,
                fill=INK,
                span_tag=SpanTag.O
            )

            y += row_height + row_height * 0.05

        return y + mm(2)

    @staticmethod
    def draw_normal(textRenderer: TextRenderer, data: InvoiceData, invoice: Invoice, d: ImageDraw, x: int, y: int, **kwargs):
        badge_w = kwargs.get("width", None)
        if badge_w is None:
            badge_w = mm(75)

        badge_h = mm(10)

        for v in data.vat:
            d.rounded_rectangle(
                [x, y, x + badge_w, y + badge_h],
                radius=mm(1),
                fill=(253, 253, 253),
                outline=LINE_MID
            )

            d.rectangle([x, y + mm(2), x + mm(1), y + badge_h - mm(2)], fill=INK)

            curr_x = x + mm(4)

            textRenderer._text(
                invoice,
                d,
                (curr_x, y + mm(1.5)),
                label="DPH",
                text=f"{v.vat_percentage}",
                end="%",
                font=textRenderer._f8b,
                fill=MUTED,
                span_tag=SpanTag.O
            )

            textRenderer._text(
                invoice,
                d,
                (curr_x, y + mm(4.5)),
                text="Základ:",
                font=textRenderer._f8,
                fill=MUTED
            )
            textRenderer._text(
                invoice,
                d,
                (curr_x + mm(10), y + mm(4.5)),
                text=fmt_money(v.vat_base),
                font=textRenderer._f9,
                fill=INK,
                span_tag=SpanTag.O
            )

            textRenderer._text_right(
                invoice,
                d,
                x + badge_w - mm(3),
                y + mm(1.5),
                text="VÝŠE DANĚ",
                font=textRenderer._f8b,
                fill=MUTED
            )
            textRenderer._text_right(
                invoice,
                d,
                x + badge_w - mm(3),
                y + mm(4.5),
                text=fmt_money(v.vat),
                font=textRenderer._f10b,
                fill=INK,
                span_tag=SpanTag.O
            )

            y += badge_h + mm(2)

        return y + mm(2)