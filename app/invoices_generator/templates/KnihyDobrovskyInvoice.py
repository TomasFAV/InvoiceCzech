from datetime import datetime
from typing import final

from PIL import Image, ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.utils.consts import _A4_H_PX, _A4_W_PX, INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG
from common.utils.utilities import mm, safe, fmt_money
from common.enumerates.SpanTag import SpanTag


@final
class KnihyDobrovskyInvoice(InvoiceTemplate):

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # Okraje
        margin_l = mm(14)
        margin_r = mm(14)
        margin_t = mm(12)
        margin_b = mm(14)

        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = _A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        def vr(x: int, y0: int, y1: int, weight: str = "mid") -> None:
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x, y0), (x, y1)], fill=color, width=3 if weight == "strong" else 2)

        # ---------------------------------------------------------------------
        # Rozměry/rozvržení (laděno podle vzoru)
        # ---------------------------------------------------------------------
        W = _A4_W_PX - margin_l - margin_r
        x0 = margin_l
        x1 = margin_l + W

        # horní rám (2 sloupce)
        top_h = mm(108)
        left_w = int(W * 0.44)
        right_w = W - left_w
        x_mid = x0 + left_w

        y = margin_t
        top_y0 = y
        top_y1 = y + top_h

        # vnější rámeček + dělení
        d.rectangle((x0, top_y0, x1, top_y1), outline=LINE_STRONG, width=2)
        vr(x_mid, top_y0, top_y1, "mid")

        # ---------------------------------------------------------------------
        # LEVÝ HORNÍ BLOK
        # ---------------------------------------------------------------------
        # Logo/hlavička levého bloku (s linkou dole)
        logo_h = mm(16)
        d.rectangle((x0, top_y0, x_mid, top_y0 + logo_h), outline=LINE_STRONG, width=2)

        textRenderer._text(invoice, (x0 + mm(10), top_y0 + mm(4)), "KNIHY DOBROVSKÝ", font=textRenderer._f13b, fill=INK)
        textRenderer._text(invoice, (x0 + mm(10), top_y0 + mm(10.2)), "Váš knihkupec s tradicí", font=textRenderer._f9, fill=MUTED)
        textRenderer._text_right(invoice, x_mid - mm(10), top_y0 + mm(10.2), "Zal. 1990", textRenderer._f9, MUTED)

        # Prodávající + identifikace
        yl = top_y0 + logo_h + mm(6)
        textRenderer._text(invoice, (x0 + mm(10), yl), "prodávající:", font=textRenderer._f10b, fill=INK)
        yl += mm(6)

        seller_name = getattr(data, "seller_name", data.supplier.name)
        seller_addr = getattr(data, "seller_address", data.supplier.address)
        seller_reg = getattr(data, "seller_register_id", data.supplier.register_id)
        seller_tax = getattr(data, "seller_tax_id", data.supplier.tax_id)

        textRenderer._text(invoice, (x0 + mm(10), yl), safe(seller_name), font=textRenderer._f11b, fill=INK)
        yl += mm(5.2)
        textRenderer._text(invoice, (x0 + mm(10), yl), safe(seller_addr), font=textRenderer._f10, fill=INK)
        yl += mm(5.2)

        textRenderer._text(invoice,
            (x0 + mm(10), yl),
            text=safe(seller_reg),
            label="identifikační číslo: ",
            font=textRenderer._f10, fill=INK,
            span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        yl += mm(5.2)

        textRenderer._text(invoice,
            (x0 + mm(10), yl),
            text=safe(seller_tax),
            label="daňové identifikační číslo plátce: ",
            font=textRenderer._f10, fill=INK,
            span_tag=SpanTag.SUPPLIER_TAX_ID)
        yl += mm(6)

        textRenderer._text(invoice, (x0 + mm(10), yl), "zhotovitel je registrován v obchodním rejstříku.", font=textRenderer._f9, fill=MUTED)
        yl += mm(10)

        # Reklamace
        textRenderer._text(invoice, (x0 + mm(10), yl), "Kam zaslat reklamaci:", font=textRenderer._f10b, fill=INK)
        yl += mm(6)

        complaints_name = getattr(data, "complaints_name", seller_name)
        complaints_addr = getattr(data, "complaints_address", seller_addr)
        complaints_email = getattr(data, "complaints_email", "reklamace@knihydobrovsky.cz")

        textRenderer._text(invoice, (x0 + mm(10), yl), safe(complaints_name), font=textRenderer._f10, fill=INK)
        yl += mm(5.2)
        textRenderer._text(invoice, (x0 + mm(10), yl), safe(complaints_addr), font=textRenderer._f10, fill=INK)
        yl += mm(5.2)
        textRenderer._text(invoice, (x0 + mm(10), yl), safe(complaints_email), font=textRenderer._f10, fill=INK)
        yl += mm(6)

        shipping = getattr(data, "shipping_method", "Zásilkovna")
        textRenderer._text(invoice, (x0 + mm(10), yl), f"Doprava: {safe(shipping)}", font=textRenderer._f10, fill=INK)

        # ---------------------------------------------------------------------
        # PRAVÝ HORNÍ BLOK (VS + doklad + odběratel + doručovací + řádky s daty)
        # ---------------------------------------------------------------------
        # 1) VS + číslo dokladu (horní pás)
        yrt0 = top_y0
        head_h = mm(20)
        d.rectangle((x_mid, yrt0, x1, yrt0 + head_h), outline=LINE_STRONG, width=2)

        textRenderer._text(invoice, (x_mid + mm(10), yrt0 + mm(5)),
                   "var. symbol (uvádějte při platbě):", font=textRenderer._f10b, fill=INK)
        textRenderer._text_right(invoice, x1 - mm(10), yrt0 + mm(5),
                         safe(data.variable_symbol), textRenderer._f11b, INK, span_tag=SpanTag.VARIABLE_SYMBOL)

        doc_label = getattr(data, "document_title", "účetní doklad č.:")
        textRenderer._text(invoice, (x_mid + mm(10), yrt0 + mm(12.5)),
                   safe(doc_label), font=textRenderer._f10b, fill=INK)
        textRenderer._text_right(invoice, x1 - mm(10), yrt0 + mm(12.5),
                         safe(data.invoice_number), textRenderer._f11b, INK, span_tag=SpanTag.INVOICE_NUMBER)

        # 2) Odběratel
        y_ob0 = yrt0 + head_h
        ob_h = mm(30)
        d.rectangle((x_mid, y_ob0, x1, y_ob0 + ob_h), outline=LINE_STRONG, width=2)

        textRenderer._text(invoice, (x_mid + mm(10), y_ob0 + mm(5)), "odběratel:", font=textRenderer._f10b, fill=INK)

        cust_name = safe(data.customer.name)
        cust_addr = safe(data.customer.address)
        cust_reg = safe(getattr(data.customer, "register_id", ""))
        cust_tax = safe(getattr(data.customer, "tax_id", ""))

        textRenderer._text(invoice, (x_mid + mm(52), y_ob0 + mm(5)), cust_name, font=textRenderer._f10, fill=INK)
        textRenderer._text(invoice, (x_mid + mm(52), y_ob0 + mm(12)), cust_addr, font=textRenderer._f10, fill=INK)

        textRenderer._text(invoice, (x_mid + mm(10), y_ob0 + mm(22)), "identifikační číslo:", font=textRenderer._f10b, fill=INK)
        last_x = textRenderer._text(invoice,
            (x_mid + mm(42), y_ob0 + mm(22)),
            cust_reg, font=textRenderer._f10, fill=INK,
            span_tag=SpanTag.CUSTOMER_REGISTER_ID
        )[0]
        last_x = textRenderer._text(invoice, (last_x + mm(5), y_ob0 + mm(22)), "dič plátce:", font=textRenderer._f10b, fill=INK)[0]
        textRenderer._text(invoice,
            (last_x + mm(3), y_ob0 + mm(22)),
            cust_tax, font=textRenderer._f10, fill=INK,
            span_tag=SpanTag.CUSTOMER_TAX_ID
        )

        # 3) Doručovací adresa
        y_del0 = y_ob0 + ob_h
        del_h = mm(22)
        d.rectangle((x_mid, y_del0, x1, y_del0 + del_h), outline=LINE_STRONG, width=2)

        textRenderer._text(invoice, (x_mid + mm(10), y_del0 + mm(5)), "Doručovací  adresa:", font=textRenderer._f10b, fill=INK)

        delivery_name = safe(getattr(data, "delivery_name", "Z-BOX"))
        delivery_addr = safe(getattr(data, "delivery_address", cust_addr))

        textRenderer._text(invoice, (x_mid + mm(52), y_del0 + mm(5)), delivery_name, font=textRenderer._f10b, fill=INK)
        textRenderer._text(invoice, (x_mid + mm(52), y_del0 + mm(12)), delivery_addr, font=textRenderer._f10, fill=INK)

        # 4) řádky s daty/úhradou/bankou
        y_dat0 = y_del0 + del_h
        d.rectangle((x_mid, y_dat0, x1, top_y1), outline=LINE_STRONG, width=2)

        yy = y_dat0 + mm(4)
        step = mm(5.2)

        def row(label: str, value: str, tag: SpanTag = SpanTag.O, undersampling: bool = True) -> None:
            nonlocal yy
            textRenderer._text(invoice, (x_mid + mm(10), yy), label, font=textRenderer._f9, fill=INK)
            textRenderer._text(invoice, (x_mid + mm(72), yy), safe(value), font=textRenderer._f9, fill=INK,
                       span_tag=tag)
            yy += step

        row("datum  vyhotovení  dokladu:", safe(data.issue_date), SpanTag.ISSUE_DATE)
        row("datum  zdanitelného  plnění:", safe(data.taxable_supply_date), SpanTag.TAXABLE_SUPPLY_DATE)

        payment_label = getattr(data, "payment_label", "online platba")
        row("Úhrada:", safe(payment_label), SpanTag.PAYMENT_TYPE)

        bank_name = getattr(data.bank_account, "name", getattr(data, "bank_name", ""))
        row("Banka:", safe(bank_name))

        acct = safe(getattr(data, "bank_account_number", getattr(data, "account_number", "")))
        row("bankovní - účtu:", acct, SpanTag.BANK_ACCOUNT_NUMBER)

        # ---------------------------------------------------------------------
        # TABULKA POLOŽEK (pod horním blokem)
        # ---------------------------------------------------------------------
        y = top_y1 + mm(10)

        headers = [
            "Předmět plnění",
            "počet/ks",
            "Cena za jedn.",
            "Celková částka",
            "Sazba DPH",
            "Částka DPH",
            "Cena celkem s DPH",
        ]
        col_ws = [0.2, 0.10, 0.14, 0.12, 0.15, 0.16, 0.13]
        col_abs = [int(round(w * W)) for w in col_ws]
        col_abs[-1] = W - sum(col_abs[:-1])
        x_cols = [x0]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        head_h2 = mm(12)
        d.rectangle((x0, y, x1, y + head_h2), outline=LINE_STRONG, width=2, fill=None)
        for i in range(1, len(x_cols)):
            vr(x_cols[i], y, y + head_h2, "mid")

        for i, h in enumerate(headers):
            if i == 0:
                textRenderer._text(invoice, (x_cols[i] + mm(6), y + mm(3)), h, font=textRenderer._f10b, fill=INK, must_have_same_width=True)
            else:
                textRenderer._text_center(invoice, x_cols[i] + col_abs[i] / 2, y + mm(2.2), h, textRenderer._f9b, INK, must_have_same_width=True)

        y += head_h2

        row_h = mm(7.5)
        for it in data.items:
            d.rectangle((x0, y, x1, y + row_h), outline=LINE_MID, width=2, fill=None)
            for i in range(1, len(x_cols)):
                vr(x_cols[i], y, y + row_h, "thin")

            desc = safe(it.description)
            qty = safe(getattr(it, "quantity", "1"))
            unit = safe(getattr(it, "unit", "ks"))
            qty_txt = f"{qty} {unit}".strip()

            ppu_wo = fmt_money(getattr(it, "ppu", getattr(it, "price_per_unit_without_vat", 0)))
            total_wo = fmt_money(getattr(it, "price_without_vat", 0))
            vat_p = safe(getattr(it, "vat_percentage", "0"))
            vat_amt = fmt_money(getattr(it, "vat", 0))
            total_w = fmt_money(getattr(it, "price_with_vat", 0))

            ty = y + mm(2.4)

            textRenderer._text(invoice, (x_cols[0] + mm(6), ty), desc, font=textRenderer._f10, fill=INK)
            textRenderer._text_center(invoice, x_cols[1] + col_abs[1] / 2, ty, qty_txt, textRenderer._f10, INK)
            textRenderer._text_right(invoice, x_cols[2] + col_abs[2] - mm(6), ty, ppu_wo, textRenderer._f10, INK)
            textRenderer._text_right(invoice, x_cols[3] + col_abs[3] - mm(6), ty, total_wo, textRenderer._f10, INK)
            textRenderer._text_center(invoice, x_cols[4] + col_abs[4] / 2, ty, f"{vat_p}%", textRenderer._f10, INK)
            textRenderer._text_right(invoice, x_cols[5] + col_abs[5] - mm(6), ty, vat_amt, textRenderer._f10, INK)
            textRenderer._text_right(invoice, x_cols[6] + col_abs[6] - mm(6), ty, total_w, textRenderer._f10, INK)

            y += row_h

        # ---------------------------------------------------------------------
        # ✅ TOTAL (celkem) pod tabulkou položek
        # ---------------------------------------------------------------------
        # linka pod tabulkou
        y += mm(6)
        hr(y, "mid", x0=x0, x1=x1)
        y += mm(5)

        total_value = fmt_money(getattr(data, "calculated_total_price", 0))

        # label vlevo + částka vpravo (tag TOTAL)
        textRenderer._text(invoice, (x0 + mm(6), y), "Celkem:", font=textRenderer._f11b, fill=INK)
        textRenderer._text_right(invoice,
            x1 - mm(6),
            y,
            total_value,
            textRenderer._f13b,
            INK,
            span_tag=SpanTag.TOTAL)

        # ---------------------------------------------------------------------
        # PATIČKA (linka + 3 bloky)
        # ---------------------------------------------------------------------
        footer_y = _A4_H_PX - margin_b - mm(16)
        hr(footer_y, "thin")

        tel = getattr(data, "supplier_phone", "+420 542220320")
        email = getattr(data, "supplier_email", "poradime@knihydobrovsky.cz")
        web = getattr(data, "supplier_web", "www.knihydobrovsky.cz")
        issued_ts = getattr(data, "issued_timestamp", datetime.now().strftime("%d.%m.%Y  %H:%M:%S"))

        textRenderer._text(invoice, (margin_l, footer_y + mm(4)), f"Tel:  {tel}", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (margin_l, footer_y + mm(9)), safe(email), font=textRenderer._f9, fill=INK)
        textRenderer._text_center(invoice, _A4_W_PX / 2, footer_y + mm(8), f"datum  vystavení:  {issued_ts}", textRenderer._f9, INK)
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, footer_y + mm(4), safe(web), textRenderer._f9, INK)
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, footer_y + mm(9), "Strana:  1", textRenderer._f9, INK)

        invoice.image = img
        return True
