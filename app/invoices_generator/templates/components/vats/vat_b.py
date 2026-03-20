from PIL.ImageDraw import ImageDraw
from PIL.ImageFont import truetype

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import fmt_money, mm
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE_MID, SUBTLE_BG


class vat_b(invoice_component):

    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        w = kwargs.get("width")
        h = kwargs.get("height")
        if not w or not h:
            return vat_b.draw_normal(inv, d, x, y, width=w)
        return vat_b.draw_scaled(inv, d, x, y, width=w, height=h)

    @staticmethod
    def _clamp(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    @staticmethod
    def draw_scaled(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        w: int = kwargs["width"]
        h: int = kwargs["height"]

        rows = max(1, len(inv.vat))

        # --- všechno jen z w/h ---
        pad_x = w * 0.02
        header_h = h * 0.22
        body_h = max(0, h - header_h)
        row_h = body_h / rows
        row_h = min(row_h, 75) #maximálně 75px

        # font ~ 55% výšky řádku (clamp kvůli extrémům)
        base_path = getattr(inv._f8, "path", None)
        size = int(vat_b._clamp(row_h * 0.55, 6, 28))
        font = truetype(base_path, size) if base_path else inv._f8

        # sloupce procenty
        col1 = x + pad_x
        col2 = x + w * 0.33
        col3 = x + w * 0.78

        # --- hlavička ---
        d.rectangle([x, y, x + w, y + header_h], fill=SUBTLE_BG)
        ty = y + header_h * 0.18
        inv._text(d, (col1, ty), "Sazba", font=font, fill=MUTED)
        inv._text(d, (col2, ty), "Základ daně", font=font, fill=MUTED)
        inv._text(d, (col3, ty), "Daň", font=font, fill=MUTED)

        # --- řádky ---
        cy = y + header_h
        for v in inv.vat:
            # linka dole v řádku
            ly = cy + size
            d.line([(x + pad_x, ly), (x + w - pad_x, ly)], fill=LINE_MID, width=1)

            inv._text(d, (col1, cy), f"{v.vat_percentage}", end="%", font=font, fill=INK,
                      span_tag=span_tags.VAT_PERCENTAGE)
            inv._text(d, (col2, cy), fmt_money(v.vat_base), font=font, fill=INK,
                      span_tag=span_tags.VAT_BASE)
            inv._text(d, (col3, cy), fmt_money(v.vat), font=font, fill=INK,
                      span_tag=span_tags.VAT)

            cy += row_h

        return y + h

    @staticmethod
    def draw_normal(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        width = kwargs.get("width") or mm(85)

        # Hlavička rekapitulace DPH
        d.rectangle([x, y, x + width, y + mm(6)], fill=SUBTLE_BG)

        # Sloupce jako původně (fixní layout)
        col_sazba = x + mm(2)
        col_zaklad = x + mm(25)
        col_dan = x + mm(65)

        inv._text(d, (col_sazba, y + mm(1)), "Sazba", font=inv._f8b, fill=MUTED)
        inv._text(d, (col_zaklad, y + mm(1)), "Základ daně", font=inv._f8b, fill=MUTED)
        inv._text(d, (col_dan, y + mm(1)), "Daň", font=inv._f8b, fill=MUTED)

        y += mm(7)

        for v in inv.vat:
            d.line([(x + mm(2), y + mm(5)), (x + width - mm(2), y + mm(5))], fill=LINE_MID, width=1)

            inv._text(d, (col_sazba, y), text=f"{v.vat_percentage}",end="%", font=inv._f10b, fill=INK,
                      span_tag=span_tags.VAT_PERCENTAGE)
            inv._text(d, (col_zaklad, y), text=fmt_money(v.vat_base), font=inv._f10, fill=INK,
                      span_tag=span_tags.VAT_BASE)
            inv._text(d, (col_dan, y), text=fmt_money(v.vat), font=inv._f10b, fill=INK,
                      span_tag=span_tags.VAT)

            y += mm(6)

        return y + mm(2)