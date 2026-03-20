from datetime import datetime
from typing import final

from PIL import Image, ImageDraw

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG
from invoices_generator.utility.utils import mm, safe, fmt_money
from invoices_generator.core.enumerates.span_tags import span_tags


@final
class knihy_dobrovsky(DInvoice):

    def generate_img(self, output_path: str) -> bool:
        # Okraje
        margin_l = mm(14)
        margin_r = mm(14)
        margin_t = mm(12)
        margin_b = mm(14)

        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        def vr(x: int, y0: int, y1: int, weight: str = "mid") -> None:
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x, y0), (x, y1)], fill=color, width=3 if weight == "strong" else 2)

        # ---------------------------------------------------------------------
        # Rozměry/rozvržení (laděno podle vzoru)
        # ---------------------------------------------------------------------
        W = self._A4_W_PX - margin_l - margin_r
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

        self._text(d, (x0 + mm(10), top_y0 + mm(4)), "KNIHY DOBROVSKÝ", font=self._f13b, fill=INK)
        self._text(d, (x0 + mm(10), top_y0 + mm(10.2)), "Váš knihkupec s tradicí", font=self._f9, fill=MUTED)
        self._draw_right(d, x_mid - mm(10), top_y0 + mm(10.2), "Zal. 1990", self._f9, MUTED)

        # Prodávající + identifikace
        yl = top_y0 + logo_h + mm(6)
        self._text(d, (x0 + mm(10), yl), "prodávající:", font=self._f10b, fill=INK)
        yl += mm(6)

        seller_name = getattr(self, "seller_name", self.supplier.name)
        seller_addr = getattr(self, "seller_address", self.supplier.address)
        seller_reg = getattr(self, "seller_register_id", self.supplier.register_id)
        seller_tax = getattr(self, "seller_tax_id", self.supplier.tax_id)

        self._text(d, (x0 + mm(10), yl), safe(seller_name), font=self._f11b, fill=INK)
        yl += mm(5.2)
        self._text(d, (x0 + mm(10), yl), safe(seller_addr), font=self._f10, fill=INK)
        yl += mm(5.2)

        self._text(
            d, (x0 + mm(10), yl),
            text=safe(seller_reg),
            label="identifikační číslo: ",
            font=self._f10, fill=INK,
            span_tag=span_tags.SUPPLIER_REGISTER_ID)
        yl += mm(5.2)

        self._text(
            d, (x0 + mm(10), yl),
            text=safe(seller_tax),
            label="daňové identifikační číslo plátce: ",
            font=self._f10, fill=INK,
            span_tag=span_tags.SUPPLIER_TAX_ID)
        yl += mm(6)

        self._text(d, (x0 + mm(10), yl), "zhotovitel je registrován v obchodním rejstříku.", font=self._f9, fill=MUTED)
        yl += mm(10)

        # Reklamace
        self._text(d, (x0 + mm(10), yl), "Kam zaslat reklamaci:", font=self._f10b, fill=INK)
        yl += mm(6)

        complaints_name = getattr(self, "complaints_name", seller_name)
        complaints_addr = getattr(self, "complaints_address", seller_addr)
        complaints_email = getattr(self, "complaints_email", "reklamace@knihydobrovsky.cz")

        self._text(d, (x0 + mm(10), yl), safe(complaints_name), font=self._f10, fill=INK)
        yl += mm(5.2)
        self._text(d, (x0 + mm(10), yl), safe(complaints_addr), font=self._f10, fill=INK)
        yl += mm(5.2)
        self._text(d, (x0 + mm(10), yl), safe(complaints_email), font=self._f10, fill=INK)
        yl += mm(6)

        shipping = getattr(self, "shipping_method", "Zásilkovna")
        self._text(d, (x0 + mm(10), yl), f"Doprava: {safe(shipping)}", font=self._f10, fill=INK)

        # ---------------------------------------------------------------------
        # PRAVÝ HORNÍ BLOK (VS + doklad + odběratel + doručovací + řádky s daty)
        # ---------------------------------------------------------------------
        # 1) VS + číslo dokladu (horní pás)
        yrt0 = top_y0
        head_h = mm(20)
        d.rectangle((x_mid, yrt0, x1, yrt0 + head_h), outline=LINE_STRONG, width=2)

        self._text(d, (x_mid + mm(10), yrt0 + mm(5)),
                   "var. symbol (uvádějte při platbě):", font=self._f10b, fill=INK)
        self._draw_right(d, x1 - mm(10), yrt0 + mm(5),
                         safe(self.variable_symbol), self._f11b, INK, span_tag=span_tags.VARIABLE_SYMBOL)

        doc_label = getattr(self, "document_title", "účetní doklad č.:")
        self._text(d, (x_mid + mm(10), yrt0 + mm(12.5)),
                   safe(doc_label), font=self._f10b, fill=INK)
        self._draw_right(d, x1 - mm(10), yrt0 + mm(12.5),
                         safe(self.invoice_number), self._f11b, INK, span_tag=span_tags.INVOICE_NUMBER)

        # 2) Odběratel
        y_ob0 = yrt0 + head_h
        ob_h = mm(30)
        d.rectangle((x_mid, y_ob0, x1, y_ob0 + ob_h), outline=LINE_STRONG, width=2)

        self._text(d, (x_mid + mm(10), y_ob0 + mm(5)), "odběratel:", font=self._f10b, fill=INK)

        cust_name = safe(self.customer.name)
        cust_addr = safe(self.customer.address)
        cust_reg = safe(getattr(self.customer, "register_id", ""))
        cust_tax = safe(getattr(self.customer, "tax_id", ""))

        self._text(d, (x_mid + mm(52), y_ob0 + mm(5)), cust_name, font=self._f10, fill=INK)
        self._text(d, (x_mid + mm(52), y_ob0 + mm(12)), cust_addr, font=self._f10, fill=INK)

        self._text(d, (x_mid + mm(10), y_ob0 + mm(22)), "identifikační číslo:", font=self._f10b, fill=INK)
        last_x = self._text(
            d, (x_mid + mm(42), y_ob0 + mm(22)),
            cust_reg, font=self._f10, fill=INK,
            span_tag=span_tags.CUSTOMER_REGISTER_ID
        )[0]
        last_x = self._text(d, (last_x + mm(5), y_ob0 + mm(22)), "dič plátce:", font=self._f10b, fill=INK)[0]
        self._text(
            d, (last_x + mm(3), y_ob0 + mm(22)),
            cust_tax, font=self._f10, fill=INK,
            span_tag=span_tags.CUSTOMER_TAX_ID
        )

        # 3) Doručovací adresa
        y_del0 = y_ob0 + ob_h
        del_h = mm(22)
        d.rectangle((x_mid, y_del0, x1, y_del0 + del_h), outline=LINE_STRONG, width=2)

        self._text(d, (x_mid + mm(10), y_del0 + mm(5)), "Doručovací  adresa:", font=self._f10b, fill=INK)

        delivery_name = safe(getattr(self, "delivery_name", "Z-BOX"))
        delivery_addr = safe(getattr(self, "delivery_address", cust_addr))

        self._text(d, (x_mid + mm(52), y_del0 + mm(5)), delivery_name, font=self._f10b, fill=INK)
        self._text(d, (x_mid + mm(52), y_del0 + mm(12)), delivery_addr, font=self._f10, fill=INK)

        # 4) řádky s daty/úhradou/bankou
        y_dat0 = y_del0 + del_h
        d.rectangle((x_mid, y_dat0, x1, top_y1), outline=LINE_STRONG, width=2)

        yy = y_dat0 + mm(4)
        step = mm(5.2)

        def row(label: str, value: str, tag: span_tags = span_tags.O, undersampling: bool = True) -> None:
            nonlocal yy
            self._text(d, (x_mid + mm(10), yy), label, font=self._f9, fill=INK)
            self._text(d, (x_mid + mm(72), yy), safe(value), font=self._f9, fill=INK,
                       span_tag=tag)
            yy += step

        row("datum  vyhotovení  dokladu:", safe(self.issue_date), span_tags.ISSUE_DATE)
        row("datum  zdanitelného  plnění:", safe(self.taxable_supply_date), span_tags.TAXABLE_SUPPLY_DATE)

        payment_label = getattr(self, "payment_label", "online platba")
        row("Úhrada:", safe(payment_label), span_tags.PAYMENT_TYPE)

        bank_name = getattr(self.bank_account, "name", getattr(self, "bank_name", ""))
        row("Banka:", safe(bank_name))

        acct = safe(getattr(self, "bank_account_number", getattr(self, "account_number", "")))
        row("bankovní - účtu:", acct, span_tags.BANK_ACCOUNT_NUMBER)

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
                self._text(d, (x_cols[i] + mm(6), y + mm(3)), h, font=self._f10b, fill=INK, must_have_same_width=True)
            else:
                self._draw_center(d, x_cols[i] + col_abs[i] / 2, y + mm(2.2), h, self._f9b, INK, must_have_same_width=True)

        y += head_h2

        row_h = mm(7.5)
        for it in self.items:
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

            self._text(d, (x_cols[0] + mm(6), ty), desc, font=self._f10, fill=INK)
            self._draw_center(d, x_cols[1] + col_abs[1] / 2, ty, qty_txt, self._f10, INK)
            self._draw_right(d, x_cols[2] + col_abs[2] - mm(6), ty, ppu_wo, self._f10, INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - mm(6), ty, total_wo, self._f10, INK)
            self._draw_center(d, x_cols[4] + col_abs[4] / 2, ty, f"{vat_p}%", self._f10, INK)
            self._draw_right(d, x_cols[5] + col_abs[5] - mm(6), ty, vat_amt, self._f10, INK)
            self._draw_right(d, x_cols[6] + col_abs[6] - mm(6), ty, total_w, self._f10, INK)

            y += row_h

        # ---------------------------------------------------------------------
        # ✅ TOTAL (celkem) pod tabulkou položek
        # ---------------------------------------------------------------------
        # linka pod tabulkou
        y += mm(6)
        hr(y, "mid", x0=x0, x1=x1)
        y += mm(5)

        total_value = fmt_money(getattr(self, "calculated_total_price", 0))

        # label vlevo + částka vpravo (tag TOTAL)
        self._text(d, (x0 + mm(6), y), "Celkem:", font=self._f11b, fill=INK)
        self._draw_right(
            d,
            x1 - mm(6),
            y,
            total_value,
            self._f13b,
            INK,
            span_tag=span_tags.TOTAL)

        # ---------------------------------------------------------------------
        # PATIČKA (linka + 3 bloky)
        # ---------------------------------------------------------------------
        footer_y = self._A4_H_PX - margin_b - mm(16)
        hr(footer_y, "thin")

        tel = getattr(self, "supplier_phone", "+420 542220320")
        email = getattr(self, "supplier_email", "poradime@knihydobrovsky.cz")
        web = getattr(self, "supplier_web", "www.knihydobrovsky.cz")
        issued_ts = getattr(self, "issued_timestamp", datetime.now().strftime("%d.%m.%Y  %H:%M:%S"))

        self._text(d, (margin_l, footer_y + mm(4)), f"Tel:  {tel}", font=self._f9, fill=INK)
        self._text(d, (margin_l, footer_y + mm(9)), safe(email), font=self._f9, fill=INK)
        self._draw_center(d, self._A4_W_PX / 2, footer_y + mm(8), f"datum  vystavení:  {issued_ts}", self._f9, INK)
        self._draw_right(d, self._A4_W_PX - margin_r, footer_y + mm(4), safe(web), self._f9, INK)
        self._draw_right(d, self._A4_W_PX - margin_r, footer_y + mm(9), "Strana:  1", self._f9, INK)

        img = self.post_process(img)
        img.save(output_path, format="PNG")
        return True
