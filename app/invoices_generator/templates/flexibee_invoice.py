from __future__ import annotations

from datetime import datetime
from typing import final

from PIL import Image, ImageDraw

from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.relationship import relationship

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG
from invoices_generator.utility.utils import mm, safe, fmt_money


@final
class flexibee_invoice(DInvoice):
    """
    Šablona ve stylu ABRA Flexi / FlexiBee (Faktura - daňový doklad),
    podle dodaného vzoru.
    """

    def generate_img(self, output_path: str) -> bool:
        # Okraje
        margin_l = mm(14)
        margin_r = mm(14)
        margin_t = mm(10)
        margin_b = mm(12)

        # Plátno
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        page_w = self._A4_W_PX - margin_l - margin_r

        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
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
        self._text(d, (margin_l, y), "Faktura - daňový doklad", font=self._f18b, fill=INK)
        # číslo vpravo nahoře
        self._draw_right(
            d,
            self._A4_W_PX - margin_r,
            y + mm(1),
            text=safe(self.invoice_number),
            font=self._f18b,
            fill=INK,
            span_tag=span_tags.INVOICE_NUMBER,        )
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
        self._text(d, (lx, ly), "Dodavatel:", font=self._f11, fill=INK)
        ly += mm(6)
        self._text(
            d,
            (lx, ly),
            text=safe(self.supplier.name),
            font=self._f14b,
            fill=INK,)
        ly += mm(6.5)
        self._text(
            d,
            (lx, ly),
            text=safe(self.supplier.address),
            font=self._f12,
            fill=INK)
        ly += mm(6)
        # město/PSČ (pokud máte rozdělené, klidně si to poskládejte v datové vrstvě do .address)
        # stát
        if getattr(self.supplier, "country", None):
            self._text(d, (lx, ly), safe(self.supplier.country.name), font=self._f12, fill=INK)
            ly += mm(6)

        # IČ/DIČ
        self._text(
            d,
            (lx, ly),
            text=safe(self.supplier.register_id),
            label="IČO: ",
            font=self._f11,
            fill=INK,
            span_tag=span_tags.SUPPLIER_REGISTER_ID)
        ly += mm(5)
        self._text(
            d,
            (lx, ly),
            text=safe(self.supplier.tax_id),
            label="DIČ: ",
            font=self._f11,
            fill=INK,
            span_tag=span_tags.SUPPLIER_TAX_ID)

        # kontakty (vzorově vlevo dole v dodavateli)
        ly += mm(4)
        self._text(d, (lx, ly), "E-mail:", font=self._f10, fill=MUTED)
        if getattr(self.supplier, "email", None):
            self._text(
                d,
                (lx + mm(24), ly),
                safe(self.supplier.email),
                font=self._f10,
                fill=INK,
                span_tag=span_tags.SUPPLIER_EMAIL if hasattr(span_tags, "SUPPLIER_EMAIL") else span_tags.O)
        ly += mm(4.2)
        self._text(d, (lx, ly), "WWW:", font=self._f10, fill=MUTED)
        if getattr(self.supplier, "web", None):
            self._text(
                d,
                (lx + mm(24), ly),
                safe(self.supplier.web),
                font=self._f10,
                fill=INK,
                span_tag=span_tags.SUPPLIER_WEB if hasattr(span_tags, "SUPPLIER_WEB") else span_tags.O)

        # PRAVÝ: Odběratel + Poštovní adresa (s výrazným rámečkem)
        rx0 = mid_x
        rx = rx0 + mm(2)
        ry = main_top + mm(4)

        # horní: Odběratel - sídlo (tenký rám uvnitř pravého sloupce)
        odb_h = mm(26)
        box(rx0, main_top, margin_l + page_w, main_top + odb_h, "thin")
        self._text(d, (rx, ry), "Odběratel - sídlo:", font=self._f11, fill=INK)

        self._text(
            d,
            (rx + mm(44), ry),
            text=safe(self.customer.name),
            font=self._f11b,
            fill=INK,
            span_tag=span_tags.CUSTOMER_NAME if hasattr(span_tags, "CUSTOMER_NAME") else span_tags.O)
        ry += mm(5.2)
        self._text(
            d,
            (rx + mm(44), ry),
            text=safe(self.customer.address),
            font=self._f11b,
            fill=INK,
            span_tag=span_tags.CUSTOMER_ADDRESS if hasattr(span_tags, "CUSTOMER_ADDRESS") else span_tags.O)
        ry += mm(7)
        self._text(
            d,
            (rx + mm(44), ry),
            text=safe(self.customer.register_id),
            label="IČO: ",
            font=self._f10,
            fill=MUTED,
            span_tag=span_tags.CUSTOMER_REGISTER_ID)
        ry += mm(4)
        self._text(
            d,
            (rx + mm(44), ry),
            text=safe(self.customer.tax_id),
            label="DIČ: ",
            font=self._f10,
            fill=MUTED,
            span_tag=span_tags.CUSTOMER_TAX_ID)

        # Poštovní adresa (silný rám)
        post_y0 = main_top + odb_h
        post_h = mm(34)
        box(rx0, post_y0, margin_l + page_w, post_y0 + post_h, "strong")
        self._text(d, (rx, post_y0 + mm(4)), "Poštovní adresa:", font=self._f11, fill=INK)

        # adresa uprostřed tučně
        addr_center_x = rx0 + (page_w // 4)  # střed pravého sloupce
        addr_y = post_y0 + mm(12)
        self._draw_center(
            d,
            addr_center_x,
            addr_y,
            text=safe(self.customer.name),
            font=self._f12b,
            fill=INK,
            span_tag=span_tags.CUSTOMER_NAME if hasattr(span_tags, "CUSTOMER_NAME") else span_tags.O)
        self._draw_center(
            d,
            addr_center_x,
            addr_y + mm(6),
            text=safe(self.customer.address),
            font=self._f12b,
            fill=INK,
            span_tag=span_tags.CUSTOMER_ADDRESS if hasattr(span_tags, "CUSTOMER_ADDRESS") else span_tags.O)

        # spodní část pravého sloupce: Místo určení + další pole
        low_y0 = post_y0 + post_h
        box(rx0, low_y0, margin_l + page_w, main_bottom, "thin")
        # vpravo dole jsou texty k datům (vzor)
        self._text(d, (rx, low_y0 + mm(4)), "Místo určení:", font=self._f11, fill=INK)
        # další řádky
        self._draw_right(d, rx + mm(40), low_y0 + mm(10), text=safe(self.issue_date), font=self._f11, fill=INK, span_tag=span_tags.ISSUE_DATE, label="Vystaveno: ")
        self._draw_right(d, rx + mm(40), low_y0 + mm(15), text=safe(self.due_date), font=self._f11b, fill=INK, span_tag=span_tags.DUE_DATE, label="Datum splatnosti: ")
        self._draw_right(
            d,
            rx+mm(40),
            low_y0 + mm(20),
            text=safe(self.taxable_supply_date),
            font=self._f11,
            fill=INK,
            span_tag=span_tags.TAXABLE_SUPPLY_DATE,label="DUZP: ")
        # levý spodní blok uvnitř hlavního boxu: Banka/účet + QR + symboly
        # oddělovač vodorovně v levém sloupci
        left_low_y0 = main_top + mm(46)
        hr(left_low_y0, "thin", x0=margin_l, x1=mid_x)

        blx = margin_l + mm(4)
        bly = left_low_y0 + mm(4)

        self._text(d, (blx, bly), "Banka:", font=self._f11, fill=INK)
        if getattr(self, "bank_account", None):
            self._text(
                d,
                (blx + mm(22), bly),
                text=safe(self.bank_account.name),
                font=self._f11,
                fill=INK,
                span_tag=span_tags.BANK_NAME if hasattr(span_tags, "BANK_NAME") else span_tags.O)

        bly += mm(5)
        self._text(d, (blx, bly), "Bankovní účet:", font=self._f11, fill=INK)
        # rámeček s účtem
        acc_box_x0 = blx + mm(30)
        acc_box_y0 = bly - mm(1.6)
        acc_box_x1 = acc_box_x0 + mm(45)
        acc_box_y1 = acc_box_y0 + mm(7)
        box(acc_box_x0, acc_box_y0, acc_box_x1, acc_box_y1, "thin")
        self._draw_center(
            d,
            (acc_box_x0 + acc_box_x1) / 2,
            bly,
            text=safe(getattr(self, "bank_account_number", "")),
            font=self._f11b,
            fill=INK,
            span_tag=span_tags.BANK_ACCOUNT_NUMBER)

        bly += mm(6)
        self._text(d, (blx, bly), "IBAN:", font=self._f11, fill=INK)
        self._text(
            d,
            (blx + mm(34), bly),
            text=safe(getattr(self, "IBAN", "")),
            font=self._f11,
            fill=INK,
            span_tag=span_tags.IBAN)

        bly += mm(5)
        self._text(d, (blx, bly), "BIC:", font=self._f11, fill=INK)
        self._text(
            d,
            (blx + mm(30), bly),
            text=safe(getattr(self.bank_account, "BIC", "")) if getattr(self, "bank_account", None) else "",
            font=self._f11,
            fill=INK,
            span_tag=span_tags.BIC)

        # symboly vlevo + QR vpravo
        sym_y = bly + mm(6)
        self._text(d, (blx, sym_y), "Var. sym.:", font=self._f11, fill=INK)
        self._text(
            d,
            (blx + mm(30), sym_y),
            text=safe(self.variable_symbol),
            font=self._f11b,
            fill=INK,
            span_tag=span_tags.VARIABLE_SYMBOL)
        sym_y += mm(5)
        self._text(d, (blx, sym_y), "Konst. sym.:", font=self._f11, fill=INK)
        self._text(
            d,
            (blx + mm(30), sym_y),
            text=safe(getattr(self, "constant_symbol", "")),
            font=self._f11b,
            fill=INK,
            span_tag=span_tags.CONSTANT_SYMBOL if hasattr(span_tags, "CONSTANT_SYMBOL") else span_tags.O)
        sym_y += mm(5)
        self._text(d, (blx, sym_y), "Spec. sym.:", font=self._f11, fill=INK)
        self._text(
            d,
            (blx + mm(30), sym_y),
            text=safe(getattr(self, "specific_symbol", "")),
            font=self._f11b,
            fill=INK,
            span_tag=span_tags.SPECIFIC_SYMBOL if hasattr(span_tags, "SPECIFIC_SYMBOL") else span_tags.O,)

        # dole vlevo: forma úhrady / doprava
        pay_y = main_bottom + mm(-12)
        self._text(d, (blx, pay_y), "Forma úhrady:", font=self._f11, fill=INK)
        self._text(
            d,
            (blx + mm(34), pay_y),
            text=safe(self.payment_type),
            font=self._f11,
            fill=INK,
            span_tag=span_tags.PAYMENT_TYPE)
        self._text(d, (blx, pay_y + mm(5)), "Způsob dopravy:", font=self._f11, fill=INK)

        # pravý spodní roh hlavního boxu: data
        dates_x = self._A4_W_PX - margin_r - mm(20)
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
                self._text(d, (x_cols[i], y), h, font=self._f11b, fill=INK, must_have_same_width=True)
            else:
                self._draw_center(d, x_cols[i] + col_w[i] / 2, y, h, self._f11b, INK, must_have_same_width=True)
        y += mm(5)
        hr(y, "thin")
        y += mm(2)

        # řádky
        row_h = mm(7)
        for it in self.items:
            y0 = y
            y1 = y0 + row_h
            # text baseline
            ty = y0 + mm(1.5)

            # 0 popis
            self._text(d, (x_cols[0], ty), safe(it.description), font=self._f11, fill=INK)

            # 1 množství
            self._draw_center(
                d,
                x_cols[1] + col_w[1] / 2,
                ty,
                safe(it.quantity),
                self._f11,
                INK,
                span_tag=span_tags.ITEM_QUANTITY if hasattr(span_tags, "ITEM_QUANTITY") else span_tags.O,
            )
            # 2 MJ
            self._draw_center(
                d,
                x_cols[2] + col_w[2] / 2,
                ty,
                safe(getattr(it, "unit", "ks")),
                self._f11,
                INK,
                span_tag=span_tags.ITEM_UNIT if hasattr(span_tags, "ITEM_UNIT") else span_tags.O,
            )
            # 3 cena za MJ
            self._draw_right(d, x_cols[3] + col_w[3], ty, fmt_money(it.ppu), self._f11, INK)
            # 4 sazba DPH
            self._draw_center(
                d,
                x_cols[4] + col_w[4] / 2,
                ty,
                f"{safe(it.vat_percentage)}",
                self._f11,
                INK,
                end="%",
            )
            # 5 základ
            self._draw_right(d, x_cols[5] + col_w[5], ty, fmt_money(it.price_without_vat), self._f11, INK)
            # 6 DPH
            self._draw_right(d, x_cols[6] + col_w[6], ty, fmt_money(it.vat), self._f11, INK)
            # 7 celkem
            self._draw_right(d, x_cols[7] + col_w[7], ty, fmt_money(it.price_with_vat), self._f11, INK)

            y = y1
            hr(y, "thin")

        # --- SOUHRN VPRAVO POD TABULKOU (Celkem řádek) ---
        y += mm(6)
        total_base_x = x_cols[5]
        total_vat_x = x_cols[6]
        total_sum_x = x_cols[7] + col_w[7]

        self._draw_right(d, total_base_x - mm(6), y, "Celkem:", self._f11b, INK)
        # základ/dph/celkem
        if len(self.vat) > 0:
            base_total = sum([float(v.vat_base) for v in self.vat])
            vat_total = sum([float(v.vat) for v in self.vat])
        else:
            base_total = getattr(self, "calculated_total_base", 0)
            vat_total = getattr(self, "calculated_total_vat", 0)

        self._draw_right(d, total_base_x + col_w[5], y, fmt_money(base_total), self._f11b, INK, span_tag=span_tags.TOTAL_BASE if hasattr(span_tags, "TOTAL_BASE") else span_tags.O)
        self._draw_right(d, total_vat_x + col_w[6], y, fmt_money(vat_total), self._f11b, INK, span_tag=span_tags.TOTAL_VAT if hasattr(span_tags, "TOTAL_VAT") else span_tags.O)
        self._draw_right(d, total_sum_x, y, fmt_money(self.calculated_total_price), self._f11b, INK, span_tag=span_tags.TOTAL)

        # --- REKAPITULACE DPH vlevo + BOX k úhradě vpravo ---
        y += mm(10)
        recap_x0 = margin_l
        recap_w = page_w * 0.55
        recap_x1 = int(recap_x0 + recap_w)

        paybox_x1 = margin_l + page_w
        paybox_w = mm(74)
        paybox_x0 = paybox_x1 - paybox_w

        self._text(d, (recap_x0, y), "Rekapitulace DPH v Kč", font=self._f11, fill=INK)
        y_re = y + mm(5)
        hr(y_re, "thin", x0=recap_x0, x1=recap_x1)
        y_re += mm(4)

        # řádky rekapitulace (stylově 2 řádky: sazba + celkem základ/dph)
        # uděláme po sazbách
        for v in self.vat:
            # "Základ 21% .... DPH 21% ...."
            self._text(d, (recap_x0, y_re), "Základ", font=self._f10, fill=INK)
            self._text(
                d,
                (recap_x0 + mm(22), y_re),
                text=fmt_money(v.vat_base),
                font=self._f10,
                fill=INK,
                span_tag=span_tags.VAT_BASE)
            self._text(d, (recap_x0 + mm(48), y_re), label="DPH", text=f"{safe(v.vat_percentage)}", end="%", span_tag=span_tags.VAT_PERCENTAGE, font=self._f10, fill=INK)
            self._draw_right(
                d,
                recap_x1,
                y_re,
                fmt_money(v.vat),
                self._f10,
                INK,
                span_tag=span_tags.VAT)
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

        self._text(d, (paybox_x0 + mm(3), pay_y0 + mm(2.6)), "Celkem k úhradě", font=self._f10, fill=INK)
        self._draw_right(d, paybox_x1 - mm(3), pay_y0 + mm(2.2), fmt_money(self.calculated_total_price), self._f10b, INK, span_tag=span_tags.TOTAL)

        self._text(d, (paybox_x0 + mm(3), pay_y0 + mm(11.6)), "Zálohy", font=self._f10, fill=INK)
        self._draw_right(d, paybox_x1 - mm(3), pay_y0 + mm(11.2), fmt_money(getattr(self, "advance_paid", 0)), self._f10b, INK)

        self._text(d, (paybox_x0 + mm(3), pay_y0 + mm(20.8)), "Zbývá uhradit [Kč]", font=self._f10, fill=INK)
        self._draw_right(
            d,
            paybox_x1 - mm(3),
            pay_y0 + mm(20.1),
            fmt_money(self.calculated_total_price),
            self._f16b,
            INK,
            span_tag=span_tags.AMOUNT_DUE if hasattr(span_tags, "AMOUNT_DUE") else span_tags.TOTAL)

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
        self._draw_center(d, (x0 + x1) / 2, sig_y + mm(3), "Razítko a podpis", self._f10, MUTED)

        # spodní texty
        foot_y = self._A4_H_PX - margin_b - mm(6)
        self._draw_center(d, self._A4_W_PX / 2, foot_y, "Vytištěno systémem ABRA Flexi.", self._f10, MUTED)
        self._draw_right(d, self._A4_W_PX - margin_r, foot_y, "Stránka 1", self._f10, MUTED)

        # Post-process (deformace/šum) – zachováno jako u ostatních šablon
        img = self.post_process(img)
        img.save(output_path, format="PNG")
        return True
