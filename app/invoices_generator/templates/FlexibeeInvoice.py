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
class FlexibeeInvoice(InvoiceTemplate):
    """
    Šablona ve stylu ABRA Flexi / FlexiBee (Faktura - daňový doklad),
    podle dodaného vzoru.
    """

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # Okraje
        margin_l = mm(14)
        margin_r = mm(14)
        margin_t = mm(10)
        margin_b = mm(12)

        # Plátno
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        page_w = _A4_W_PX - margin_l - margin_r

        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = _A4_W_PX - margin_r if x1 is None else x1
            color = LINE_STRONG if weight == "strong" else (LINE_MID if weight == "mid" else LINE)
            w = 4 if weight == "strong" else (2 if weight == "mid" else 1)
            d.line([(x0, y), (x1, y)], fill=color, width=w)

        def vr(x: int, y0: int, y1: int, weight: str = "mid") -> None:
            color = LINE_STRONG if weight == "strong" else (LINE_MID if weight == "mid" else LINE)
            w = 4 if weight == "strong" else (2 if weight == "mid" else 1)
            d.line([(x, y0), (x, y1)], fill=color, width=w)

        def box(x0: int, y0: int, x1: int, y1: int, weight: str = "mid", fill=None) -> None:
            color = LINE_STRONG if weight == "strong" else (LINE_MID if weight == "mid" else LINE)
            w = 4 if weight == "strong" else (2 if weight == "mid" else 1)
            d.rectangle((x0, y0, x1, y1), outline=color, width=w, fill=fill)

        y = margin_t

        # --- HLAVIČKA ---
        textRenderer._text(invoice, (margin_l, y), "Faktura - daňový doklad", font=textRenderer._f18b, fill=INK)
        # číslo vpravo nahoře
        textRenderer._text_right(invoice,
            _A4_W_PX - margin_r,
            y + mm(1),
            text=safe(data.invoice_number),
            font=textRenderer._f18b,
            fill=INK,
            span_tag=SpanTag.INVOICE_NUMBER,        )
        y += mm(8)
        hr(y, "strong")
        y += mm(2)

        # --- HLAVNÍ BLOK (2 sloupce) ---
        main_top = y
        main_h = mm(100)
        main_bottom = main_top + main_h
        box(margin_l, main_top, margin_l + page_w, main_bottom, "thin")
        mid_x = margin_l + page_w // 2
        vr(mid_x, main_top, main_bottom, "mid")

        # LEVÝ: Dodavatel
        lx = margin_l + mm(4)
        ly = main_top + mm(4)
        textRenderer._text(invoice, (lx, ly), "Dodavatel:", font=textRenderer._f11, fill=INK)
        ly += mm(6)
        textRenderer._text(invoice,
            (lx, ly),
            text=safe(data.supplier.name),
            font=textRenderer._f14b,
            fill=INK,)
        ly += mm(6.5)
        textRenderer._text(invoice,
            (lx, ly),
            text=safe(data.supplier.address),
            font=textRenderer._f12,
            fill=INK)
        ly += mm(6)
        # město/PSČ (pokud máte rozdělené, klidně si to poskládejte v datové vrstvě do .address)
        # stát
        if getattr(data.supplier, "country", None):
            textRenderer._text(invoice, (lx, ly), safe(data.supplier.country.name), font=textRenderer._f12, fill=INK)
            ly += mm(6)

        # IČ/DIČ
        textRenderer._text(invoice,
            (lx, ly),
            text=safe(data.supplier.register_id),
            label="IČO: ",
            font=textRenderer._f11,
            fill=INK,
            span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        ly += mm(5)
        textRenderer._text(invoice,
            (lx, ly),
            text=safe(data.supplier.tax_id),
            label="DIČ: ",
            font=textRenderer._f11,
            fill=INK,
            span_tag=SpanTag.SUPPLIER_TAX_ID)

        # kontakty (vzorově vlevo dole v dodavateli)
        ly += mm(4)
        textRenderer._text(invoice, (lx, ly), "E-mail:", font=textRenderer._f10, fill=MUTED)
        if getattr(data.supplier, "email", None):
            textRenderer._text(invoice,
                (lx + mm(24), ly),
                safe(data.supplier.email),
                font=textRenderer._f10,
                fill=INK,
                span_tag=SpanTag.SUPPLIER_EMAIL if hasattr(SpanTag, "SUPPLIER_EMAIL") else SpanTag.O)
        ly += mm(4.2)
        textRenderer._text(invoice, (lx, ly), "WWW:", font=textRenderer._f10, fill=MUTED)
        if getattr(data.supplier, "web", None):
            textRenderer._text(invoice,
                (lx + mm(24), ly),
                safe(data.supplier.web),
                font=textRenderer._f10,
                fill=INK,
                span_tag=SpanTag.SUPPLIER_WEB if hasattr(SpanTag, "SUPPLIER_WEB") else SpanTag.O)

        # PRAVÝ: Odběratel + Poštovní adresa (s výrazným rámečkem)
        rx0 = mid_x
        rx = rx0 + mm(2)
        ry = main_top + mm(4)

        # horní: Odběratel - sídlo (tenký rám uvnitř pravého sloupce)
        odb_h = mm(26)
        box(rx0, main_top, margin_l + page_w, main_top + odb_h, "thin")
        textRenderer._text(invoice, (rx, ry), "Odběratel - sídlo:", font=textRenderer._f11, fill=INK)

        textRenderer._text(invoice,
            (rx + mm(44), ry),
            text=safe(data.customer.name),
            font=textRenderer._f11b,
            fill=INK,
            span_tag=SpanTag.CUSTOMER_NAME if hasattr(SpanTag, "CUSTOMER_NAME") else SpanTag.O)
        ry += mm(5.2)
        textRenderer._text(invoice,
            (rx + mm(44), ry),
            text=safe(data.customer.address),
            font=textRenderer._f11b,
            fill=INK,
            span_tag=SpanTag.CUSTOMER_ADDRESS if hasattr(SpanTag, "CUSTOMER_ADDRESS") else SpanTag.O)
        ry += mm(7)
        textRenderer._text(invoice,
            (rx + mm(44), ry),
            text=safe(data.customer.register_id),
            label="IČO: ",
            font=textRenderer._f10,
            fill=MUTED,
            span_tag=SpanTag.CUSTOMER_REGISTER_ID)
        ry += mm(4)
        textRenderer._text(invoice,
            (rx + mm(44), ry),
            text=safe(data.customer.tax_id),
            label="DIČ: ",
            font=textRenderer._f10,
            fill=MUTED,
            span_tag=SpanTag.CUSTOMER_TAX_ID)

        # Poštovní adresa (silný rám)
        post_y0 = main_top + odb_h
        post_h = mm(34)
        box(rx0, post_y0, margin_l + page_w, post_y0 + post_h, "strong")
        textRenderer._text(invoice, (rx, post_y0 + mm(4)), "Poštovní adresa:", font=textRenderer._f11, fill=INK)

        # adresa uprostřed tučně
        addr_center_x = rx0 + (page_w // 4)  # střed pravého sloupce
        addr_y = post_y0 + mm(12)
        textRenderer._text_center(invoice,
            addr_center_x,
            addr_y,
            text=safe(data.customer.name),
            font=textRenderer._f12b,
            fill=INK,
            span_tag=SpanTag.CUSTOMER_NAME if hasattr(SpanTag, "CUSTOMER_NAME") else SpanTag.O)
        textRenderer._text_center(invoice,
            addr_center_x,
            addr_y + mm(6),
            text=safe(data.customer.address),
            font=textRenderer._f12b,
            fill=INK,
            span_tag=SpanTag.CUSTOMER_ADDRESS if hasattr(SpanTag, "CUSTOMER_ADDRESS") else SpanTag.O)

        # spodní část pravého sloupce: Místo určení + další pole
        low_y0 = post_y0 + post_h
        box(rx0, low_y0, margin_l + page_w, main_bottom, "thin")
        # vpravo dole jsou texty k datům (vzor)
        textRenderer._text(invoice, (rx, low_y0 + mm(4)), "Místo určení:", font=textRenderer._f11, fill=INK)
        # další řádky
        textRenderer._text_right(invoice, rx + mm(40), low_y0 + mm(10), text=safe(data.issue_date), font=textRenderer._f11, fill=INK, span_tag=SpanTag.ISSUE_DATE, label="Vystaveno: ")
        textRenderer._text_right(invoice, rx + mm(40), low_y0 + mm(15), text=safe(data.due_date), font=textRenderer._f11b, fill=INK, span_tag=SpanTag.DUE_DATE, label="Datum splatnosti: ")
        textRenderer._text_right(invoice,
            rx+mm(40),
            low_y0 + mm(20),
            text=safe(data.taxable_supply_date),
            font=textRenderer._f11,
            fill=INK,
            span_tag=SpanTag.TAXABLE_SUPPLY_DATE,label="DUZP: ")
        # levý spodní blok uvnitř hlavního boxu: Banka/účet + QR + symboly
        # oddělovač vodorovně v levém sloupci
        left_low_y0 = main_top + mm(46)
        hr(left_low_y0, "thin", x0=margin_l, x1=mid_x)

        blx = margin_l + mm(4)
        bly = left_low_y0 + mm(4)

        textRenderer._text(invoice, (blx, bly), "Banka:", font=textRenderer._f11, fill=INK)
        if getattr(data, "bank_account", None):
            textRenderer._text(invoice,
                (blx + mm(22), bly),
                text=safe(data.bank_account.name),
                font=textRenderer._f11,
                fill=INK,
                span_tag=SpanTag.BANK_NAME if hasattr(SpanTag, "BANK_NAME") else SpanTag.O)

        bly += mm(5)
        textRenderer._text(invoice, (blx, bly), "Bankovní účet:", font=textRenderer._f11, fill=INK)
        # rámeček s účtem
        acc_box_x0 = blx + mm(30)
        acc_box_y0 = bly - mm(1.6)
        acc_box_x1 = acc_box_x0 + mm(45)
        acc_box_y1 = acc_box_y0 + mm(7)
        box(acc_box_x0, acc_box_y0, acc_box_x1, acc_box_y1, "thin")
        textRenderer._text_center(invoice,
            (acc_box_x0 + acc_box_x1) / 2,
            bly,
            text=safe(getattr(data, "bank_account_number", "")),
            font=textRenderer._f11b,
            fill=INK,
            span_tag=SpanTag.BANK_ACCOUNT_NUMBER)

        bly += mm(6)
        textRenderer._text(invoice, (blx, bly), "IBAN:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice,
            (blx + mm(34), bly),
            text=safe(getattr(data, "IBAN", "")),
            font=textRenderer._f11,
            fill=INK,
            span_tag=SpanTag.IBAN)

        bly += mm(5)
        textRenderer._text(invoice, (blx, bly), "BIC:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice,
            (blx + mm(30), bly),
            text=safe(getattr(data.bank_account, "BIC", "")) if getattr(data, "bank_account", None) else "",
            font=textRenderer._f11,
            fill=INK,
            span_tag=SpanTag.BIC)

        # symboly vlevo + QR vpravo
        sym_y = bly + mm(6)
        textRenderer._text(invoice, (blx, sym_y), "Var. sym.:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice,
            (blx + mm(30), sym_y),
            text=safe(data.variable_symbol),
            font=textRenderer._f11b,
            fill=INK,
            span_tag=SpanTag.VARIABLE_SYMBOL)
        sym_y += mm(5)
        textRenderer._text(invoice, (blx, sym_y), "Konst. sym.:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice,
            (blx + mm(30), sym_y),
            text=safe(getattr(data, "constant_symbol", "")),
            font=textRenderer._f11b,
            fill=INK,
            span_tag=SpanTag.CONSTANT_SYMBOL if hasattr(SpanTag, "CONSTANT_SYMBOL") else SpanTag.O)
        sym_y += mm(5)
        textRenderer._text(invoice, (blx, sym_y), "Spec. sym.:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice,
            (blx + mm(30), sym_y),
            text=safe(getattr(data, "specific_symbol", "")),
            font=textRenderer._f11b,
            fill=INK,
            span_tag=SpanTag.SPECIFIC_SYMBOL if hasattr(SpanTag, "SPECIFIC_SYMBOL") else SpanTag.O,)

        # dole vlevo: forma úhrady / doprava
        pay_y = main_bottom + mm(-12)
        textRenderer._text(invoice, (blx, pay_y), "Forma úhrady:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice,
            (blx + mm(34), pay_y),
            text=safe(data.payment_type),
            font=textRenderer._f11,
            fill=INK,
            span_tag=SpanTag.PAYMENT_TYPE)
        textRenderer._text(invoice, (blx, pay_y + mm(5)), "Způsob dopravy:", font=textRenderer._f11, fill=INK)

        # pravý spodní roh hlavního boxu: data
        dates_x = _A4_W_PX - margin_r - mm(20)
        dates_y = main_bottom - mm(18)
        

        # --- TABULKA POLOŽEK ---
        y = main_bottom + mm(25)
        headers = ["Označení dodávky", "Množství", "MJ", "Cena za MJ", "Sazba DPH", "Základ", "DPH", "Celkem"]
        col_fracs = [0.2, 0.10, 0.06, 0.12, 0.10, 0.15, 0.15, 0.12]
        col_w = [int(round(page_w * f)) for f in col_fracs]
        # dorovnání posledního sloupce, aby seděla šířka
        col_w[-1] = page_w - sum(col_w[:-1])

        x_cols = [margin_l]
        for w in col_w[:-1]:
            x_cols.append(x_cols[-1] + w)

        # header linka a názvy
        hr(y, "thin")
        y += mm(2)
        for i, h in enumerate(headers):
            if i == 0:
                textRenderer._text(invoice, (x_cols[i], y), h, font=textRenderer._f11b, fill=INK, must_have_same_width=True)
            else:
                textRenderer._text_center(invoice, x_cols[i] + col_w[i] / 2, y, h, textRenderer._f11b, INK, must_have_same_width=True)
        y += mm(5)
        hr(y, "thin")
        y += mm(2)

        # řádky
        row_h = mm(7)
        for it in data.items:
            y0 = y
            y1 = y0 + row_h
            # text baseline
            ty = y0 + mm(1.5)

            # 0 popis
            textRenderer._text(invoice, (x_cols[0], ty), safe(it.description), font=textRenderer._f11, fill=INK)

            # 1 množství
            textRenderer._text_center(invoice,
                x_cols[1] + col_w[1] / 2,
                ty,
                safe(it.quantity),
                textRenderer._f11,
                INK,
                span_tag=SpanTag.ITEM_QUANTITY if hasattr(SpanTag, "ITEM_QUANTITY") else SpanTag.O,
            )
            # 2 MJ
            textRenderer._text_center(invoice,
                x_cols[2] + col_w[2] / 2,
                ty,
                safe(getattr(it, "unit", "ks")),
                textRenderer._f11,
                INK,
                span_tag=SpanTag.ITEM_UNIT if hasattr(SpanTag, "ITEM_UNIT") else SpanTag.O,
            )
            # 3 cena za MJ
            textRenderer._text_right(invoice, x_cols[3] + col_w[3], ty, fmt_money(it.ppu), textRenderer._f11, INK)
            # 4 sazba DPH
            textRenderer._text_center(invoice,
                x_cols[4] + col_w[4] / 2,
                ty,
                f"{safe(it.vat_percentage)}",
                textRenderer._f11,
                INK,
                end="%",
            )
            # 5 základ
            textRenderer._text_right(invoice, x_cols[5] + col_w[5], ty, fmt_money(it.price_without_vat), textRenderer._f11, INK)
            # 6 DPH
            textRenderer._text_right(invoice, x_cols[6] + col_w[6], ty, fmt_money(it.vat), textRenderer._f11, INK)
            # 7 celkem
            textRenderer._text_right(invoice, x_cols[7] + col_w[7], ty, fmt_money(it.price_with_vat), textRenderer._f11, INK)

            y = y1
            hr(y, "thin")

        # --- SOUHRN VPRAVO POD TABULKOU (Celkem řádek) ---
        y += mm(6)
        total_base_x = x_cols[5]
        total_vat_x = x_cols[6]
        total_sum_x = x_cols[7] + col_w[7]

        textRenderer._text_right(invoice, total_base_x - mm(6), y, "Celkem:", textRenderer._f11b, INK)
        # základ/dph/celkem
        if len(data.vat) > 0:
            base_total = sum([float(v.vat_base) for v in data.vat])
            vat_total = sum([float(v.vat) for v in data.vat])
        else:
            base_total = getattr(data, "calculated_total_base", 0)
            vat_total = getattr(data, "calculated_total_vat", 0)

        textRenderer._text_right(invoice, total_base_x + col_w[5], y, fmt_money(base_total), textRenderer._f11b, INK, span_tag=SpanTag.TOTAL_BASE if hasattr(SpanTag, "TOTAL_BASE") else SpanTag.O)
        textRenderer._text_right(invoice, total_vat_x + col_w[6], y, fmt_money(vat_total), textRenderer._f11b, INK, span_tag=SpanTag.TOTAL_VAT if hasattr(SpanTag, "TOTAL_VAT") else SpanTag.O)
        textRenderer._text_right(invoice, total_sum_x, y, fmt_money(data.calculated_total_price), textRenderer._f11b, INK, span_tag=SpanTag.TOTAL)

        # --- REKAPITULACE DPH vlevo + BOX k úhradě vpravo ---
        y += mm(10)
        recap_x0 = margin_l
        recap_w = page_w * 0.55
        recap_x1 = int(recap_x0 + recap_w)

        paybox_x1 = margin_l + page_w
        paybox_w = mm(74)
        paybox_x0 = paybox_x1 - paybox_w

        textRenderer._text(invoice, (recap_x0, y), "Rekapitulace DPH v Kč", font=textRenderer._f11, fill=INK)
        y_re = y + mm(5)
        hr(y_re, "thin", x0=recap_x0, x1=recap_x1)
        y_re += mm(4)

        # řádky rekapitulace (stylově 2 řádky: sazba + celkem základ/dph)
        # uděláme po sazbách
        for v in data.vat:
            # "Základ 21% .... DPH 21% ...."
            textRenderer._text(invoice, (recap_x0, y_re), "Základ", font=textRenderer._f10, fill=INK)
            textRenderer._text(invoice,
                (recap_x0 + mm(22), y_re),
                text=fmt_money(v.vat_base),
                font=textRenderer._f10,
                fill=INK,
                span_tag=SpanTag.O)
            textRenderer._text(invoice, (recap_x0 + mm(48), y_re), label="DPH", text=f"{safe(v.vat_percentage)}", end="%", span_tag=SpanTag.O, font=textRenderer._f10, fill=INK)
            textRenderer._text_right(invoice,
                recap_x1,
                y_re,
                fmt_money(v.vat),
                textRenderer._f10,
                INK,
                span_tag=SpanTag.O)
            # vztahy base/vat k sazbě
            # (v téhle šabloně nemáme přímo id textu sazby, tak vztahy necháme jen pokud si je chcete doplnit)
            y_re += mm(6)

        hr(y_re - mm(2), "thin", x0=recap_x0, x1=recap_x1)

        # box "Celkem k úhradě" vpravo
        pay_y0 = y - mm(2)
        pay_y1 = pay_y0 + mm(26)
        box(paybox_x0, pay_y0, paybox_x1, pay_y1, "mid")
        # vnitřní dělení
        hr(pay_y0 + mm(9), "thin", x0=paybox_x0, x1=paybox_x1)
        hr(pay_y0 + mm(18), "thin", x0=paybox_x0, x1=paybox_x1)
        vr(paybox_x0 + mm(38), pay_y0, pay_y1, "thin")

        textRenderer._text(invoice, (paybox_x0 + mm(3), pay_y0 + mm(2.6)), "Celkem k úhradě", font=textRenderer._f10, fill=INK)
        textRenderer._text_right(invoice, paybox_x1 - mm(3), pay_y0 + mm(2.2), fmt_money(data.calculated_total_price), textRenderer._f10b, INK, span_tag=SpanTag.TOTAL)

        textRenderer._text(invoice, (paybox_x0 + mm(3), pay_y0 + mm(11.6)), "Zálohy", font=textRenderer._f10, fill=INK)
        textRenderer._text_right(invoice, paybox_x1 - mm(3), pay_y0 + mm(11.2), fmt_money(getattr(data, "advance_paid", 0)), textRenderer._f10b, INK)

        textRenderer._text(invoice, (paybox_x0 + mm(3), pay_y0 + mm(20.8)), "Zbývá uhradit [Kč]", font=textRenderer._f10, fill=INK)
        textRenderer._text_right(invoice,
            paybox_x1 - mm(3),
            pay_y0 + mm(20.1),
            fmt_money(data.calculated_total_price),
            textRenderer._f16b,
            INK,
            span_tag=SpanTag.AMOUNT_DUE if hasattr(SpanTag, "AMOUNT_DUE") else SpanTag.TOTAL)

        # --- PODPIS + PATIČKA ---
        y = pay_y1 + mm(26)
        # linka pro razítko/podpis
        sig_y = y
        # "čárkovaná" linka
        x0 = margin_l + page_w * 0.55
        x1 = margin_l + page_w
        step = 10
        for x in range(int(x0), int(x1), step * 2):
            d.line([(x, sig_y), (min(x + step, x1), sig_y)], fill=LINE_MID, width=2)
        textRenderer._text_center(invoice, (x0 + x1) / 2, sig_y + mm(3), "Razítko a podpis", textRenderer._f10, MUTED)

        # spodní texty
        foot_y = _A4_H_PX - margin_b - mm(6)
        textRenderer._text_center(invoice, _A4_W_PX / 2, foot_y, "Vytištěno systémem ABRA Flexi.", textRenderer._f10, MUTED)
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, foot_y, "Stránka 1", textRenderer._f10, MUTED)

        
        invoice.image = img
        return True
