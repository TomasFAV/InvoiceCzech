from PIL.ImageDraw import ImageDraw
from PIL.ImageFont import truetype

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer

from common.data.InvoiceComponent import InvoiceComponent
from common.enumerates.SpanTag import SpanTag
from common.utils.utilities import (
    fit_line_bounding_box_font,
    mm,
    safe,
    get_random_style,
    draw_styled_rect,
)
from common.utils.consts import INK, MUTED, TMOBILE_PINK


class CompanyB(InvoiceComponent):    

    def render(textRenderer:TextRenderer, data:InvoiceData, invoice:Invoice, x: int, y: int, **kwargs):
        d: ImageDraw = ImageDraw(invoice.image)

        supplier: bool = kwargs.get("supplier", True)
        width: int | None = kwargs.get("width", None)
        height: int | None = kwargs.get("height", None)

        if not width:
            width = mm(85)

        if not height:
            height = mm(70)

        values = data.supplier if supplier else data.customer

        # Základní parametry (fallback bez width/height)
        card_width = mm(75)
        space = mm(4)

        # Najdeme max velikost fontu, aby se vešly nejdelší řádky
        things_to_be_written = [
            safe(values.name).upper(),
            f"IČ: {safe(values.register_id)}",
            f"daňové identifikační číslo: {safe(values.tax_id)}",
            f"{safe(values.address)}",
            f"Telefonní spojení: {safe(values.phone)}",
        ]

        max_font_size = textRenderer._f16b.size
        for thing in things_to_be_written:
            _, font_size = fit_line_bounding_box_font(
                thing,
                width,
                textRenderer._f12.path,
                default_font_size=25,
                min_font_size=5,
            )
            max_font_size = min(max_font_size, font_size)



        # Škálování dle boxu, pokud je daný
        if width is not None and height is not None:
            card_width = width

            # vertikální rozestupy: aby se to „nelepilo“ ani v malém boxu
            number_of_lines_target = 8
            space = min(float(height) / number_of_lines_target, float(mm(5)))

        # Fonty – radši vždy vytvořit z path (spolehlivé)
        # max_font_size je „největší“; ostatní o kousek menší
        scaled_f11b = truetype(textRenderer._f11b.path, int(max_font_size))
        scaled_f10 = truetype(textRenderer._f10.path, int(max_font_size) - 1)
        scaled_f9  = truetype(textRenderer._f9.path,  int(max_font_size) - 2)
        scaled_f8b = truetype(textRenderer._f8b.path, int(max_font_size) - 3)

        # Hlavička
        label_text = "DODAVATEL" if supplier else "ODBĚRATEL"
        accent_color = TMOBILE_PINK if supplier else INK

        y_start = y
        style = get_random_style()

        # 1) Horní lišta
        draw_styled_rect(d, (x, y, x + card_width, y + space), style)
        textRenderer._text(
            invoice,
            d,
            (x + mm(3), y),
            text=label_text,
            font=scaled_f8b,
            fill=MUTED,
        )

        y += space * 1.1

        # 2) Název firmy
        textRenderer._text(invoice, (x, y), text=safe(values.name).upper(), font=scaled_f11b, fill=INK)

        # 3) Adresa + linka
        y += 1.2 * space
        line_y_start = y

        address_x = x + mm(4)
        textRenderer._text(invoice, (address_x, y), text=safe(values.address), font=scaled_f10, fill=INK)
        y += space

        # IČ / DIČ se span tagy dle role
        reg_tag = SpanTag.SUPPLIER_REGISTER_ID if supplier else SpanTag.CUSTOMER_REGISTER_ID
        tax_tag = SpanTag.SUPPLIER_TAX_ID if supplier else SpanTag.CUSTOMER_TAX_ID

        textRenderer._text(
            invoice,
            d, (address_x, y),
            label="IČ: ",
            text=safe(values.register_id),
            font=scaled_f9,
            fill=MUTED,
            span_tag=reg_tag
        )
        y += space

        textRenderer._text(
            invoice,
            d, (address_x, y),
            label="DIČ: ",
            text=safe(values.tax_id),
            font=scaled_f9,
            fill=MUTED,
            span_tag=tax_tag
        )

        # Volitelné řádky, jen pokud je výška boxu a zbývá místo
        if height is not None:
            bottom = y_start + height

            # Telefon
            if y + 2.3 * space < bottom:
                y += space * 1.1
                textRenderer._text(
                    invoice,
                    d, (address_x, y),
                    label="Telefonní spojení: ",
                    text=safe(values.phone),
                    font=scaled_f9,
                    fill=MUTED
                )

            # Email
            if y + 2.0 * space < bottom:
                y += space
                textRenderer._text(
                    invoice,
                    d, (address_x, y),
                    label="E-mail: ",
                    text=safe(values.mail),
                    font=scaled_f9,
                    fill=MUTED
                )

        # Vertikální linka (šířka může být taky škálovaná)
        d.line(
            [(x + mm(1), line_y_start), (x + mm(1), y)],
            fill=accent_color,
            width=1
        )

        return y + mm(5)