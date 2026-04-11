from __future__ import annotations
from typing import final

from PIL import Image, ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.invoice.renderers.TextRenderer import TextRenderer
from common.enumerates.SpanTag import SpanTag

from common.utils.consts import _A4_H_PX, _A4_W_PX, INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG
from common.utils.utilities import mm, safe, fmt_money


@final
class OreaHotelInvoice(InvoiceTemplate):
    """
    Šablona podobná: OREA / Hotelový účet – daňový doklad
    - velký header, číslo vpravo nahoře
    - 2 velké boxy: Dodavatel + Odběratel
    - bankovní spojení vlevo, platební metadata vpravo
    - order-id řádek
    - tabulka položek (ubytování, poplatek z pobytu, …)
    - "Celkem s DPH" velký text napravo pod tabulkou
    - Přehled úhrad + Rekapitulace DPH
    - box "Částka k proplacení" vpravo dole
    """

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # Okraje (trochu menší, aby to sedělo k poslanému vzoru)
        margin_l = mm(10)
        margin_r = mm(10)
        margin_t = mm(10)
        margin_b = mm(10)

        W = _A4_W_PX
        H = _A4_H_PX

        img = Image.new("RGB", (W, H), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        # ---- helpers ---------------------------------------------------------
        def hline(y: int, x0: int | None = None, x1: int | None = None, weight: str = "mid") -> None:
            x0 = margin_l if x0 is None else x0
            x1 = W - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            width = 3 if weight == "strong" else (2 if weight == "mid" else 1)
            d.line([(x0, y), (x1, y)], fill=color, width=width)

        def vline(x: int, y0: int, y1: int, weight: str = "mid") -> None:
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            width = 3 if weight == "strong" else (2 if weight == "mid" else 1)
            d.line([(x, y0), (x, y1)], fill=color, width=width)

        def rect(x0: int, y0: int, x1: int, y1: int, weight: str = "mid", fill=None) -> None:
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            width = 3 if weight == "strong" else (2 if weight == "mid" else 1)
            d.rectangle((x0, y0, x1, y1), outline=color, width=width, fill=fill)

        # ---- layout constants ------------------------------------------------
        content_x0 = margin_l
        content_x1 = W - margin_r
        content_w = content_x1 - content_x0

        y = margin_t

        # =====================================================================
        # HLAVIČKA
        # =====================================================================
        header_h = mm(28)
        rect(content_x0, y, content_x1, y + header_h, weight="strong", fill=None)

        # „OREA“ vlevo + podtitul (hotel)
        # (logo řeš jen jako text; pro variabilitu datasetu občas přepínej velikost/rozestupy)
        textRenderer._text(invoice, (content_x0 + mm(6), y + mm(6)), "O R E A", font=textRenderer._f18b, fill=INK)
        textRenderer._text(invoice, (content_x0 + mm(6), y + mm(14)), safe(getattr(data, "supplier_branch", "Hotel Angelo\nPraha")), font=textRenderer._f10, fill=MUTED)

        # Titul dokumentu
        textRenderer._text(invoice,
            (content_x0 + mm(55), y + mm(7)),
            "Hotelový účet - daňový doklad",
            font=textRenderer._f16b,
            fill=INK)

        # Číslo faktury pod titulem (vlevo ve středu)
        # tag: INVOICE_NUMBER
        inv_no = safe(getattr(data, "invoice_number", ""))
        textRenderer._text(invoice, 
            (content_x0 + mm(55), y + mm(16)),
            f"{inv_no}",
            label="Číslo: ",
            font=textRenderer._f11,
            fill=INK,
            span_tag=SpanTag.INVOICE_NUMBER)

        # Číslo faktury v boxu vpravo nahoře (jako ve vzoru)
        box_w = mm(38)
        box_h = mm(8)
        bx1 = content_x1 - mm(6)
        bx0 = bx1 - box_w
        by0 = y + mm(4)
        by1 = by0 + box_h
        rect(bx0, by0, bx1, by1, weight="mid", fill=None)
        textRenderer._text_center(invoice,
            (bx0 + bx1) / 2,
            by0 + mm(1.2),
            inv_no,
            font=textRenderer._f11b,
            fill=INK,
            span_tag=SpanTag.INVOICE_NUMBER)

        y += header_h

        # =====================================================================
        # 2 SLOUPCE: DODAVATEL / ODBĚRATEL
        # =====================================================================
        block_h = mm(80)
        rect(content_x0, y, content_x1, y + block_h, weight="strong", fill=None)

        split_x = content_x0 + int(content_w * 0.56)
        vline(split_x, y, y + block_h, weight="strong")

        pad = mm(6)

        # ---- levý blok: Dodavatel + Provozovna + Bankovní spojení ------------
        lx0, lx1 = content_x0, split_x
        ly0 = y
        cur_y = ly0 + pad

        textRenderer._text(invoice, (lx0 + pad, cur_y), "Dodavatel:", font=textRenderer._f12b, fill=INK)
        cur_y += mm(6)

        # Dodavatel – volitelně s tagy na IČ/DIČ
        textRenderer._text(invoice, (lx0 + pad, cur_y), safe(data.supplier.name), font=textRenderer._f11b, fill=INK)
        cur_y += mm(5.2)
        textRenderer._text(invoice, (lx0 + pad, cur_y), safe(data.supplier.address), font=textRenderer._f11, fill=INK)
        cur_y += mm(5.2)

        # IČO/DIČ (tagy)
        textRenderer._text(invoice, (lx0 + pad, cur_y), "IČO", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, (lx0 + pad + mm(44), cur_y), safe(data.supplier.register_id), font=textRenderer._f11, fill=INK,
                   span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        cur_y += mm(5.2)

        textRenderer._text(invoice, (lx0 + pad, cur_y), "DIČ", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, (lx0 + pad + mm(44), cur_y), safe(data.supplier.tax_id), font=textRenderer._f11, fill=INK,
                   span_tag=SpanTag.SUPPLIER_TAX_ID)
        cur_y += mm(6.5)

        # Provozovna
        textRenderer._text(invoice, (lx0 + pad, cur_y), "Provozovna", font=textRenderer._f12b, fill=INK)
        cur_y += mm(6)
        textRenderer._text(invoice, (lx0 + pad, cur_y), safe(getattr(data, "supplier_branch_name", data.supplier.name)), font=textRenderer._f11, fill=INK)
        cur_y += mm(5.2)
        textRenderer._text(invoice, (lx0 + pad, cur_y), safe(getattr(data, "supplier_branch_address", data.supplier.address)), font=textRenderer._f11, fill=INK)
        cur_y += mm(7)

        # Bankovní spojení (CZK/EUR – můžeš generovat víc účtů)
        textRenderer._text(invoice, (lx0 + pad, cur_y), "Bankovní spojení", font=textRenderer._f12b, fill=INK)
        cur_y += mm(6)

        # 1) CZK účet
        acct = safe(getattr(data, "bank_account_number", ""))
        iban = safe(getattr(data, "IBAN", ""))
        bic = safe(getattr(data.bank_account, "BIC", "")) if getattr(data, "bank_account", None) else ""

        textRenderer._text(invoice, (lx0 + pad, cur_y), "CZK", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, (lx0 + pad + mm(38), cur_y), acct, font=textRenderer._f11, fill=INK,
                   span_tag=SpanTag.BANK_ACCOUNT_NUMBER)
        cur_y += mm(5.0)

        textRenderer._text(invoice, (lx0 + pad, cur_y), "IBAN", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, (lx0 + pad + mm(38), cur_y), iban, font=textRenderer._f11, fill=INK,
                   span_tag=SpanTag.IBAN)
        cur_y += mm(5.0)

        textRenderer._text(invoice, (lx0 + pad, cur_y), "SWIFT", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, (lx0 + pad + mm(38), cur_y), safe(bic), font=textRenderer._f11, fill=INK,
                   span_tag=SpanTag.BIC)

        # ---- pravý blok: Odběratel + platební metadata -----------------------
        rx0, rx1 = split_x, content_x1
        ry0 = y
        cur2_y = ry0 + pad

        textRenderer._text(invoice, (rx0 + pad, cur2_y), "Odběratel - plátce", font=textRenderer._f12b, fill=INK)
        cur2_y += mm(7)

        textRenderer._text(invoice, (rx0 + pad, cur2_y), safe(data.customer.name), font=textRenderer._f11b, fill=INK)
        cur2_y += mm(5.2)
        textRenderer._text(invoice, (rx0 + pad, cur2_y), safe(data.customer.address), font=textRenderer._f11, fill=INK)
        cur2_y += mm(7)

        textRenderer._text(invoice, (rx0 + pad, cur2_y), "IČO", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, (rx0 + pad + mm(44), cur2_y), safe(data.customer.register_id), font=textRenderer._f11, fill=INK,
                   span_tag=SpanTag.CUSTOMER_REGISTER_ID)
        cur2_y += mm(5.2)
        textRenderer._text(invoice, (rx0 + pad, cur2_y), "DIČ", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, (rx0 + pad + mm(44), cur2_y), safe(data.customer.tax_id), font=textRenderer._f11, fill=INK,
                   span_tag=SpanTag.CUSTOMER_TAX_ID)
        cur2_y += mm(9)

        # Platební metadata (způsob, datum, splatnost, DUZP, VS)
        # Rozvrh jako ve vzoru: label vlevo, value vpravo
        meta_x_label = rx0 + pad
        meta_x_val = rx0 + mm(62)

        def meta_row(label: str, value: str, tag: SpanTag = SpanTag.O) -> None:
            nonlocal cur2_y
            textRenderer._text(invoice, (meta_x_label, cur2_y), label, font=textRenderer._f11, fill=INK)
            textRenderer._text(invoice, (meta_x_val, cur2_y), safe(value), font=textRenderer._f11b, fill=INK,
                       span_tag=tag)
            cur2_y += mm(5.2)

        meta_row("Způsob úhrady:", safe(getattr(data.payment_type, "value", getattr(data, "payment_type", "Kartou"))), SpanTag.PAYMENT_TYPE)
        meta_row("Datum:", safe(getattr(data, "issue_date", "")), SpanTag.ISSUE_DATE)
        meta_row("Splatnost:", safe(getattr(data, "due_date", "")), SpanTag.DUE_DATE)
        meta_row("DUZP:", safe(getattr(data, "taxable_supply_date", getattr(data, "issue_date", ""))), SpanTag.TAXABLE_SUPPLY_DATE)
        meta_row("Variabilní symbol:", safe(getattr(data, "variable_symbol", inv_no)), SpanTag.VARIABLE_SYMBOL)

        y += block_h

        # =====================================================================
        # ŘÁDEK: Číslo objednávky
        # =====================================================================
        y += mm(2)
        order_h = mm(12)
        rect(content_x0, y, content_x1, y + order_h, weight="strong", fill=None)

        order_id = safe(getattr(data, "order_number", getattr(data, "booking_id", "")))
        textRenderer._text(invoice, (content_x0 + pad, y + mm(3.5)), "Číslo objednávky:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, (content_x0 + mm(55), y + mm(3.5)), order_id, font=textRenderer._f11, fill=INK,
                   span_tag=SpanTag.ORDER_NUMBER if hasattr(SpanTag, "ORDER_NUMBER") else SpanTag.O)

        y += order_h

        # =====================================================================
        # TABULKA POLOŽEK
        # =====================================================================
        y += mm(2)
        table_top = y
        table_h_head = mm(9)

        rect(content_x0, y, content_x1, y + len(data.items)*mm(8)+mm(15), weight="strong", fill=None)  # rámec celé sekce (výška se dopočte níž)

        # sloupce podobné vzoru: Položka | Od | Do | Mj. | %DPH | Základ DPH | DPH | Celkem s DPH | (volitelně EUR)
        headers = ["Položka", "Od", "Do", "Mj.", "%DPH", "Základ DPH", "DPH", "Celkem s DPH"]
        col_fracs = [0.33, 0.09, 0.09, 0.06, 0.07, 0.12, 0.10, 0.14]  # součet 1.0
        col_ws = [int(content_w * f) for f in col_fracs]
        xs = [content_x0]
        for w_ in col_ws[:-1]:
            xs.append(xs[-1] + w_)

        # header linka
        hline(y + table_h_head, content_x0, content_x1, weight="strong")

        # vertical lines
        for i in range(1, len(xs)):
            vline(xs[i], y, y + table_h_head + mm(26), weight="mid")

        # header text
        for i, h in enumerate(headers):
            if i == 0:
                textRenderer._text(invoice, (xs[i] + mm(2), y + mm(2.2)), h, font=textRenderer._f10b, fill=INK, must_have_same_width=True)
            elif i in (1, 2, 3, 4):
                textRenderer._text_center(invoice, xs[i] + col_ws[i] / 2, y + mm(2.2), h, textRenderer._f10b, INK, must_have_same_width=True)
            else:
                textRenderer._text_center(invoice, xs[i] + col_ws[i] / 2, y + mm(2.2), h, textRenderer._f10b, INK, must_have_same_width=True)

        y += table_h_head

        # rows
        row_h = mm(7)
        max_rows = min(len(data.items), 6)  # pro 1 stránku; pro multi-page si to rozděl
        for idx in range(max_rows):
            it = data.items[idx]
            y_row_top = y
            y_row_mid = y + mm(1.6)

            # row separator
            hline(y + row_h, content_x0, content_x1, weight="thin")

            # values (přizpůsob si položkám; u hotelu často období od-do)
            desc = safe(getattr(it, "description", ""))
            dfrom = safe(getattr(it, "date_from", getattr(it, "from_date", "")))
            dto = safe(getattr(it, "date_to", getattr(it, "to_date", "")))
            mj = safe(getattr(it, "unit", getattr(it, "quantity", "1")))
            vatp = safe(getattr(it, "vat_percentage", ""))
            base = fmt_money(getattr(it, "price_without_vat", getattr(it, "vat_base", 0)))
            vatv = fmt_money(getattr(it, "vat", 0))
            total = fmt_money(getattr(it, "price_with_vat", getattr(it, "total", 0)))

            # draw cells
            textRenderer._text(invoice, (xs[0] + mm(2), y_row_mid), desc, font=textRenderer._f10, fill=INK)
            textRenderer._text_center(invoice, xs[1] + col_ws[1] / 2, y_row_mid, dfrom, textRenderer._f10, INK)
            textRenderer._text_center(invoice, xs[2] + col_ws[2] / 2, y_row_mid, dto, textRenderer._f10, INK)
            textRenderer._text_center(invoice, xs[3] + col_ws[3] / 2, y_row_mid, mj, textRenderer._f10, INK)
            textRenderer._text_center(invoice, xs[4] + col_ws[4] / 2, y_row_mid, f"{vatp}%", textRenderer._f10, INK,
                              span_tag=SpanTag.O)

            textRenderer._text_right(invoice, xs[5] + col_ws[5] - mm(2), y_row_mid, base, textRenderer._f10, INK,
                             span_tag=SpanTag.O)
            textRenderer._text_right(invoice, xs[6] + col_ws[6] - mm(2), y_row_mid, vatv, textRenderer._f10, INK,
                             span_tag=SpanTag.O)
            textRenderer._text_right(invoice, xs[7] + col_ws[7] - mm(2), y_row_mid, total, textRenderer._f10, INK)

            y += row_h

        # after table
        y += mm(4)

        # =====================================================================
        # VELKÝ SOUČET "Celkem s DPH" (napravo, jako ve vzoru)
        # =====================================================================
        # Částka celkem – tag TOTAL
        total_val = fmt_money(getattr(data, "calculated_total_price", getattr(data, "total", 0)))
        textRenderer._text(invoice, (content_x0 + int(content_w * 0.62), y), "Celkem s DPH:", font=textRenderer._f14b, fill=INK)
        textRenderer._text_right(invoice,
            content_x1 - mm(2),
            y,
            f"{total_val}",
            end=f"{data.currency.value if hasattr(data.currency, 'value') else data.currency}",
            font=textRenderer._f14b,
            fill=INK,
            span_tag=SpanTag.TOTAL)

        y += mm(14)

        # =====================================================================
        # PŘEHLED ÚHRAD
        # =====================================================================
        section_w = int(content_w * 0.62)
        sx0 = content_x0
        sx1 = sx0 + section_w

        textRenderer._text(invoice, (sx0, y), "PŘEHLED ÚHRAD", font=textRenderer._f12b, fill=INK)
        y += mm(6)
        hline(y, sx0, sx1, "mid")
        y += mm(3)

        # malá tabulka: Způsob úhrady | Uhrazeno
        # (pro dataset stačí 1 řádek)
        textRenderer._text(invoice, (sx0 + mm(2), y), "Způsob úhrady", font=textRenderer._f10b, fill=INK)
        textRenderer._text_right(invoice, sx1 - mm(2), y, "Uhrazeno", textRenderer._f10b, INK)
        y += mm(4.5)
        hline(y, sx0, sx1, "thin")
        y += mm(2.5)

        pay = safe(getattr(data.payment_type, "value", getattr(data, "payment_type", "Kartou")))
        textRenderer._text(invoice, (sx0 + mm(2), y), pay, font=textRenderer._f10, fill=INK, span_tag=SpanTag.PAYMENT_TYPE)
        textRenderer._text_right(invoice, sx1 - mm(2), y, total_val, textRenderer._f10, INK)
        y += mm(7)

        # =====================================================================
        # REKAPITULACE DPH
        # =====================================================================
        textRenderer._text(invoice, (sx0, y), "REKAPITULACE DPH", font=textRenderer._f12b, fill=INK)
        y += mm(6)
        hline(y, sx0, sx1, "mid")
        y += mm(3)

        # hlavička
        textRenderer._text(invoice, (sx0 + mm(2), y), "Sazba", font=textRenderer._f10b, fill=INK)
        textRenderer._text_center(invoice, sx0 + section_w * 0.55, y, "Základ DPH", textRenderer._f10b, INK)
        textRenderer._text_right(invoice, sx1 - mm(2), y, "DPH", textRenderer._f10b, INK)
        y += mm(4.5)
        hline(y, sx0, sx1, "thin")
        y += mm(2.5)

        # řádky DPH
        for v in getattr(data, "vat", []):
            perc = safe(getattr(v, "vat_percentage", ""))
            base = fmt_money(getattr(v, "vat_base", 0))
            vatv = fmt_money(getattr(v, "vat", 0))

            # sazba
            _, perc_id = textRenderer._text(invoice, (sx0 + mm(2), y), f"{perc}%", font=textRenderer._f10, fill=INK,
                                   span_tag=SpanTag.O)
            # základ
            _, base_id = textRenderer._text_right(invoice, sx0 + section_w * 0.78, y, base, textRenderer._f10, INK,
                                          span_tag=SpanTag.O)
            # dph
            _, vat_id = textRenderer._text_right(invoice, sx1 - mm(2), y, vatv, textRenderer._f10, INK,
                                         span_tag=SpanTag.O)

            
            y += mm(5.5)

        # součet řádek
        hline(y, sx0, sx1, "thin")
        y += mm(2.5)
        textRenderer._text(invoice, (sx0 + mm(2), y), "Celkem", font=textRenderer._f10b, fill=INK)
        textRenderer._text_right(invoice, sx1 - mm(2), y, total_val, textRenderer._f10b, INK, span_tag=SpanTag.TOTAL)
        y += mm(10)

        # =====================================================================
        # SPODNÍ ČÁST + BOX "Částka k proplacení"
        # =====================================================================
        bottom_y = H - margin_b - mm(42)

        # podpisy / poznámky vlevo
        textRenderer._text(invoice, (content_x0, bottom_y+mm(10)), "Fakturu vystavil:", font=textRenderer._f10, fill=INK)
        textRenderer._text(invoice, (content_x0, bottom_y + mm(15)), safe(getattr(data, "issuer", "ABROZ (upravil: ABROZ)")), font=textRenderer._f10, fill=INK)

        # box částka k proplacení vpravo dole
        due_box_w = mm(64)
        due_box_h = mm(28)
        dbx1 = content_x1
        dbx0 = dbx1 - due_box_w
        dby1 = H - margin_b - mm(8)
        dby0 = dby1 - due_box_h
        rect(dbx0, dby0, dbx1, dby1, weight="strong", fill=None)

        textRenderer._text_center(invoice, (dbx0 + dbx1) / 2, dby0 + mm(4), "Částka k proplacení", textRenderer._f12b, INK)
        # typicky 0,00 pokud uhrazeno; tag můžeš dát TOTAL_DUE pokud ho máš
        due_val = fmt_money(getattr(data, "amount_due", 0))
        textRenderer._text_center(invoice,
            (dbx0 + dbx1) / 2,
            dby0 + mm(12),
            f"{due_val} {data.currency.value if hasattr(data.currency, 'value') else data.currency}",
            textRenderer._f12b,
            INK,
            span_tag=SpanTag.TOTAL_DUE if hasattr(SpanTag, "TOTAL_DUE") else SpanTag.O)

        # linky "Převzal" / "Dodavatel"
        line_y = H - margin_b - mm(8)
        hline(line_y, content_x0, content_x1, "strong")
        textRenderer._text(invoice, (content_x0, line_y + mm(3)), "Převzal:", font=textRenderer._f10, fill=INK)
        textRenderer._text_center(invoice, (content_x0 + content_x1) / 2, line_y + mm(3), "Dodavatel:", textRenderer._f10, INK)

        # =====================================================================
        # Post-process (scan/noise) + save
        # =====================================================================
        
        invoice.image = img
        return True
