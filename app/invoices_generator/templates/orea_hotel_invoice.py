from __future__ import annotations
from typing import final

from PIL import Image, ImageDraw

from invoice_annotator.utils.GRelationship import GRelationship
from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.enumerates.relationship_types import relationship_types

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, BOX_BG
from invoices_generator.utility.utils import mm, safe, fmt_money


@final
class orea_hotel_invoice(DInvoice):
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

    def generate_img(self, output_path: str) -> bool:
        # Okraje (trochu menší, aby to sedělo k poslanému vzoru)
        margin_l = mm(10)
        margin_r = mm(10)
        margin_t = mm(10)
        margin_b = mm(10)

        W = self._A4_W_PX
        H = self._A4_H_PX

        img = Image.new("RGB", (W, H), BG)
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
        self._text(d, (content_x0 + mm(6), y + mm(6)), "O R E A", font=self._f18b, fill=INK)
        self._text(d, (content_x0 + mm(6), y + mm(14)), safe(getattr(self, "supplier_branch", "Hotel Angelo\nPraha")), font=self._f10, fill=MUTED)

        # Titul dokumentu
        self._text(
            d,
            (content_x0 + mm(55), y + mm(7)),
            "Hotelový účet - daňový doklad",
            font=self._f16b,
            fill=INK)

        # Číslo faktury pod titulem (vlevo ve středu)
        # tag: INVOICE_NUMBER
        inv_no = safe(getattr(self, "invoice_number", ""))
        self._text(
            d,
            (content_x0 + mm(55), y + mm(16)),
            f"{inv_no}",
            label="Číslo: ",
            font=self._f11,
            fill=INK,
            span_tag=span_tags.INVOICE_NUMBER)

        # Číslo faktury v boxu vpravo nahoře (jako ve vzoru)
        box_w = mm(38)
        box_h = mm(8)
        bx1 = content_x1 - mm(6)
        bx0 = bx1 - box_w
        by0 = y + mm(4)
        by1 = by0 + box_h
        rect(bx0, by0, bx1, by1, weight="mid", fill=None)
        self._draw_center(
            d,
            (bx0 + bx1) / 2,
            by0 + mm(1.2),
            inv_no,
            font=self._f11b,
            fill=INK,
            span_tag=span_tags.INVOICE_NUMBER)

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

        self._text(d, (lx0 + pad, cur_y), "Dodavatel:", font=self._f12b, fill=INK)
        cur_y += mm(6)

        # Dodavatel – volitelně s tagy na IČ/DIČ
        self._text(d, (lx0 + pad, cur_y), safe(self.supplier.name), font=self._f11b, fill=INK)
        cur_y += mm(5.2)
        self._text(d, (lx0 + pad, cur_y), safe(self.supplier.address), font=self._f11, fill=INK)
        cur_y += mm(5.2)

        # IČO/DIČ (tagy)
        self._text(d, (lx0 + pad, cur_y), "IČO", font=self._f11, fill=INK)
        self._text(d, (lx0 + pad + mm(44), cur_y), safe(self.supplier.register_id), font=self._f11, fill=INK,
                   span_tag=span_tags.SUPPLIER_REGISTER_ID)
        cur_y += mm(5.2)

        self._text(d, (lx0 + pad, cur_y), "DIČ", font=self._f11, fill=INK)
        self._text(d, (lx0 + pad + mm(44), cur_y), safe(self.supplier.tax_id), font=self._f11, fill=INK,
                   span_tag=span_tags.SUPPLIER_TAX_ID)
        cur_y += mm(6.5)

        # Provozovna
        self._text(d, (lx0 + pad, cur_y), "Provozovna", font=self._f12b, fill=INK)
        cur_y += mm(6)
        self._text(d, (lx0 + pad, cur_y), safe(getattr(self, "supplier_branch_name", self.supplier.name)), font=self._f11, fill=INK)
        cur_y += mm(5.2)
        self._text(d, (lx0 + pad, cur_y), safe(getattr(self, "supplier_branch_address", self.supplier.address)), font=self._f11, fill=INK)
        cur_y += mm(7)

        # Bankovní spojení (CZK/EUR – můžeš generovat víc účtů)
        self._text(d, (lx0 + pad, cur_y), "Bankovní spojení", font=self._f12b, fill=INK)
        cur_y += mm(6)

        # 1) CZK účet
        acct = safe(getattr(self, "bank_account_number", ""))
        iban = safe(getattr(self, "IBAN", ""))
        bic = safe(getattr(self.bank_account, "BIC", "")) if getattr(self, "bank_account", None) else ""

        self._text(d, (lx0 + pad, cur_y), "CZK", font=self._f11, fill=INK)
        self._text(d, (lx0 + pad + mm(38), cur_y), acct, font=self._f11, fill=INK,
                   span_tag=span_tags.BANK_ACCOUNT_NUMBER)
        cur_y += mm(5.0)

        self._text(d, (lx0 + pad, cur_y), "IBAN", font=self._f11, fill=INK)
        self._text(d, (lx0 + pad + mm(38), cur_y), iban, font=self._f11, fill=INK,
                   span_tag=span_tags.IBAN)
        cur_y += mm(5.0)

        self._text(d, (lx0 + pad, cur_y), "SWIFT", font=self._f11, fill=INK)
        self._text(d, (lx0 + pad + mm(38), cur_y), safe(bic), font=self._f11, fill=INK,
                   span_tag=span_tags.BIC)

        # ---- pravý blok: Odběratel + platební metadata -----------------------
        rx0, rx1 = split_x, content_x1
        ry0 = y
        cur2_y = ry0 + pad

        self._text(d, (rx0 + pad, cur2_y), "Odběratel - plátce", font=self._f12b, fill=INK)
        cur2_y += mm(7)

        self._text(d, (rx0 + pad, cur2_y), safe(self.customer.name), font=self._f11b, fill=INK)
        cur2_y += mm(5.2)
        self._text(d, (rx0 + pad, cur2_y), safe(self.customer.address), font=self._f11, fill=INK)
        cur2_y += mm(7)

        self._text(d, (rx0 + pad, cur2_y), "IČO", font=self._f11, fill=INK)
        self._text(d, (rx0 + pad + mm(44), cur2_y), safe(self.customer.register_id), font=self._f11, fill=INK,
                   span_tag=span_tags.CUSTOMER_REGISTER_ID)
        cur2_y += mm(5.2)
        self._text(d, (rx0 + pad, cur2_y), "DIČ", font=self._f11, fill=INK)
        self._text(d, (rx0 + pad + mm(44), cur2_y), safe(self.customer.tax_id), font=self._f11, fill=INK,
                   span_tag=span_tags.CUSTOMER_TAX_ID)
        cur2_y += mm(9)

        # Platební metadata (způsob, datum, splatnost, DUZP, VS)
        # Rozvrh jako ve vzoru: label vlevo, value vpravo
        meta_x_label = rx0 + pad
        meta_x_val = rx0 + mm(62)

        def meta_row(label: str, value: str, tag: span_tags = span_tags.O) -> None:
            nonlocal cur2_y
            self._text(d, (meta_x_label, cur2_y), label, font=self._f11, fill=INK)
            self._text(d, (meta_x_val, cur2_y), safe(value), font=self._f11b, fill=INK,
                       span_tag=tag)
            cur2_y += mm(5.2)

        meta_row("Způsob úhrady:", safe(getattr(self.payment_type, "value", getattr(self, "payment_type", "Kartou"))), span_tags.PAYMENT_TYPE)
        meta_row("Datum:", safe(getattr(self, "issue_date", "")), span_tags.ISSUE_DATE)
        meta_row("Splatnost:", safe(getattr(self, "due_date", "")), span_tags.DUE_DATE)
        meta_row("DUZP:", safe(getattr(self, "taxable_supply_date", getattr(self, "issue_date", ""))), span_tags.TAXABLE_SUPPLY_DATE)
        meta_row("Variabilní symbol:", safe(getattr(self, "variable_symbol", inv_no)), span_tags.VARIABLE_SYMBOL)

        y += block_h

        # =====================================================================
        # ŘÁDEK: Číslo objednávky
        # =====================================================================
        y += mm(2)
        order_h = mm(12)
        rect(content_x0, y, content_x1, y + order_h, weight="strong", fill=None)

        order_id = safe(getattr(self, "order_number", getattr(self, "booking_id", "")))
        self._text(d, (content_x0 + pad, y + mm(3.5)), "Číslo objednávky:", font=self._f11, fill=INK)
        self._text(d, (content_x0 + mm(55), y + mm(3.5)), order_id, font=self._f11, fill=INK,
                   span_tag=span_tags.ORDER_NUMBER if hasattr(span_tags, "ORDER_NUMBER") else span_tags.O)

        y += order_h

        # =====================================================================
        # TABULKA POLOŽEK
        # =====================================================================
        y += mm(2)
        table_top = y
        table_h_head = mm(9)

        rect(content_x0, y, content_x1, y + len(self.items)*mm(8)+mm(15), weight="strong", fill=None)  # rámec celé sekce (výška se dopočte níž)

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
                self._text(d, (xs[i] + mm(2), y + mm(2.2)), h, font=self._f10b, fill=INK, must_have_same_width=True)
            elif i in (1, 2, 3, 4):
                self._draw_center(d, xs[i] + col_ws[i] / 2, y + mm(2.2), h, self._f10b, INK, must_have_same_width=True)
            else:
                self._draw_center(d, xs[i] + col_ws[i] / 2, y + mm(2.2), h, self._f10b, INK, must_have_same_width=True)

        y += table_h_head

        # rows
        row_h = mm(7)
        max_rows = min(len(self.items), 6)  # pro 1 stránku; pro multi-page si to rozděl
        for idx in range(max_rows):
            it = self.items[idx]
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
            self._text(d, (xs[0] + mm(2), y_row_mid), desc, font=self._f10, fill=INK)
            self._draw_center(d, xs[1] + col_ws[1] / 2, y_row_mid, dfrom, self._f10, INK)
            self._draw_center(d, xs[2] + col_ws[2] / 2, y_row_mid, dto, self._f10, INK)
            self._draw_center(d, xs[3] + col_ws[3] / 2, y_row_mid, mj, self._f10, INK)
            self._draw_center(d, xs[4] + col_ws[4] / 2, y_row_mid, f"{vatp}%", self._f10, INK,
                              span_tag=span_tags.VAT_PERCENTAGE)

            self._draw_right(d, xs[5] + col_ws[5] - mm(2), y_row_mid, base, self._f10, INK,
                             span_tag=span_tags.VAT_BASE)
            self._draw_right(d, xs[6] + col_ws[6] - mm(2), y_row_mid, vatv, self._f10, INK,
                             span_tag=span_tags.VAT)
            self._draw_right(d, xs[7] + col_ws[7] - mm(2), y_row_mid, total, self._f10, INK)

            y += row_h

        # after table
        y += mm(4)

        # =====================================================================
        # VELKÝ SOUČET "Celkem s DPH" (napravo, jako ve vzoru)
        # =====================================================================
        # Částka celkem – tag TOTAL
        total_val = fmt_money(getattr(self, "calculated_total_price", getattr(self, "total", 0)))
        self._text(d, (content_x0 + int(content_w * 0.62), y), "Celkem s DPH:", font=self._f14b, fill=INK)
        self._draw_right(
            d,
            content_x1 - mm(2),
            y,
            f"{total_val}",
            end=f"{self.currency.value if hasattr(self.currency, 'value') else self.currency}",
            font=self._f14b,
            fill=INK,
            span_tag=span_tags.TOTAL)

        y += mm(14)

        # =====================================================================
        # PŘEHLED ÚHRAD
        # =====================================================================
        section_w = int(content_w * 0.62)
        sx0 = content_x0
        sx1 = sx0 + section_w

        self._text(d, (sx0, y), "PŘEHLED ÚHRAD", font=self._f12b, fill=INK)
        y += mm(6)
        hline(y, sx0, sx1, "mid")
        y += mm(3)

        # malá tabulka: Způsob úhrady | Uhrazeno
        # (pro dataset stačí 1 řádek)
        self._text(d, (sx0 + mm(2), y), "Způsob úhrady", font=self._f10b, fill=INK)
        self._draw_right(d, sx1 - mm(2), y, "Uhrazeno", self._f10b, INK)
        y += mm(4.5)
        hline(y, sx0, sx1, "thin")
        y += mm(2.5)

        pay = safe(getattr(self.payment_type, "value", getattr(self, "payment_type", "Kartou")))
        self._text(d, (sx0 + mm(2), y), pay, font=self._f10, fill=INK, span_tag=span_tags.PAYMENT_TYPE)
        self._draw_right(d, sx1 - mm(2), y, total_val, self._f10, INK)
        y += mm(7)

        # =====================================================================
        # REKAPITULACE DPH
        # =====================================================================
        self._text(d, (sx0, y), "REKAPITULACE DPH", font=self._f12b, fill=INK)
        y += mm(6)
        hline(y, sx0, sx1, "mid")
        y += mm(3)

        # hlavička
        self._text(d, (sx0 + mm(2), y), "Sazba", font=self._f10b, fill=INK)
        self._draw_center(d, sx0 + section_w * 0.55, y, "Základ DPH", self._f10b, INK)
        self._draw_right(d, sx1 - mm(2), y, "DPH", self._f10b, INK)
        y += mm(4.5)
        hline(y, sx0, sx1, "thin")
        y += mm(2.5)

        # řádky DPH
        for v in getattr(self, "vat", []):
            perc = safe(getattr(v, "vat_percentage", ""))
            base = fmt_money(getattr(v, "vat_base", 0))
            vatv = fmt_money(getattr(v, "vat", 0))

            # sazba
            _, perc_id = self._text(d, (sx0 + mm(2), y), f"{perc}%", font=self._f10, fill=INK,
                                   span_tag=span_tags.VAT_PERCENTAGE)
            # základ
            _, base_id = self._draw_right(d, sx0 + section_w * 0.78, y, base, self._f10, INK,
                                          span_tag=span_tags.VAT_BASE)
            # dph
            _, vat_id = self._draw_right(d, sx1 - mm(2), y, vatv, self._f10, INK,
                                         span_tag=span_tags.VAT)

            # vztahy (pokud je používáš)
            self.append_relationship(GRelationship(None ,base_id, perc_id, relationship_types.BASE_OF))
            self.append_relationship(GRelationship(None, vat_id, perc_id, relationship_types.VAT_OF))

            y += mm(5.5)

        # součet řádek
        hline(y, sx0, sx1, "thin")
        y += mm(2.5)
        self._text(d, (sx0 + mm(2), y), "Celkem", font=self._f10b, fill=INK)
        self._draw_right(d, sx1 - mm(2), y, total_val, self._f10b, INK, span_tag=span_tags.TOTAL)
        y += mm(10)

        # =====================================================================
        # SPODNÍ ČÁST + BOX "Částka k proplacení"
        # =====================================================================
        bottom_y = H - margin_b - mm(42)

        # podpisy / poznámky vlevo
        self._text(d, (content_x0, bottom_y+mm(10)), "Fakturu vystavil:", font=self._f10, fill=INK)
        self._text(d, (content_x0, bottom_y + mm(15)), safe(getattr(self, "issuer", "ABROZ (upravil: ABROZ)")), font=self._f10, fill=INK)

        # box částka k proplacení vpravo dole
        due_box_w = mm(64)
        due_box_h = mm(28)
        dbx1 = content_x1
        dbx0 = dbx1 - due_box_w
        dby1 = H - margin_b - mm(8)
        dby0 = dby1 - due_box_h
        rect(dbx0, dby0, dbx1, dby1, weight="strong", fill=None)

        self._draw_center(d, (dbx0 + dbx1) / 2, dby0 + mm(4), "Částka k proplacení", self._f12b, INK)
        # typicky 0,00 pokud uhrazeno; tag můžeš dát TOTAL_DUE pokud ho máš
        due_val = fmt_money(getattr(self, "amount_due", 0))
        self._draw_center(
            d,
            (dbx0 + dbx1) / 2,
            dby0 + mm(12),
            f"{due_val} {self.currency.value if hasattr(self.currency, 'value') else self.currency}",
            self._f12b,
            INK,
            span_tag=span_tags.TOTAL_DUE if hasattr(span_tags, "TOTAL_DUE") else span_tags.O)

        # linky "Převzal" / "Dodavatel"
        line_y = H - margin_b - mm(8)
        hline(line_y, content_x0, content_x1, "strong")
        self._text(d, (content_x0, line_y + mm(3)), "Převzal:", font=self._f10, fill=INK)
        self._draw_center(d, (content_x0 + content_x1) / 2, line_y + mm(3), "Dodavatel:", self._f10, INK)

        # =====================================================================
        # Post-process (scan/noise) + save
        # =====================================================================
        img = self.post_process(img)
        img.save(output_path, format="PNG")
        return True
