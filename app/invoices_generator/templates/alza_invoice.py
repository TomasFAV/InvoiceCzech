from datetime import datetime
from typing import final

from PIL import Image, ImageDraw

from invoice_annotator.utils.GRelationship import GRelationship
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words
from invoices_generator.utility.utils import safe, fmt_money


@final
class alza_invoice(DInvoice):


    def generate_img(self, output_path: str) -> bool:
        # Okraje (podle .page padding)
        margin_l = mm(14)
        margin_r = mm(14)
        margin_t = mm(12)
        margin_b = mm(14)

        # Plátno
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        # Pomocné čáry
        def hr(y:int, weight:str="mid", x0:int|None=None, x1:int|None=None)->None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        # Start Y
        y = margin_t

        # --- HLAVIČKA ---
        # Logo/jméno dodavatele vlevo
        self._text(d,(margin_l, y), text=safe(self.supplier.name), font=self._f16b, fill=INK)

        # Titul (centrovaný blok vpravo části)
        title_center_x = self._A4_W_PX // 2
        self._draw_center(d, title_center_x, y, text=f"{safe(self.invoice_number)}", font=self._f17b, fill=INK, label="Faktura -", span_tag=span_tags.INVOICE_NUMBER)
        self._draw_center(d, title_center_x, y + mm(12), "záruční a dodací list -", self._f12, MUTED)

        y += mm(18)
        local_x = margin_l
        # --- Prodávající ---
        self._text(d,(margin_l, y), text=f"Prodávající: {safe(self.supplier.name)} {self.supplier.type.value}", font=self._f12b,
                fill=INK)
        
        y += mm(5.2)
        local_x, _ = self._text(d,(local_x, y),
                text=f"{safe(self.supplier.address)},",
                font=self._f11, fill=INK)
        
        local_x, _ = self._text(d,(local_x, y),
                text=f"{safe(self.supplier.register_id)}",
                font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_REGISTER_ID, label="IČ: ", end=",")

        local_x, _ = self._text(d,(local_x, y),
                text=f"{safe(self.supplier.tax_id)}",
                font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_TAX_ID, label="DIČ: ", end=",")
        

        local_x, _ = self._text(d,(local_x, y),
                text=f"internet: www.{safe(self.supplier.name)}.cz, kontakt: www.{safe(self.supplier.name)}.cz/kontakt",
                font=self._f11, fill=INK)

        y += mm(4)

        y += mm(1.5)

        # --- Dva sloupce ---
        col_gap = mm(24)
        table_w = self._A4_W_PX - margin_l - margin_r
        col_w = (table_w - col_gap) // 2
        left_x = margin_l
        right_x = margin_l + col_w + col_gap

        # Levý blok
        self._text(d,(left_x, y), text="Daňový doklad:", font=self._f12b, fill=INK)
        y_left = y + mm(6)

        kv_label_w = mm(60)

        def kv_row(x:int, y_:int, label:str, value:str, bold:bool=True, tag: span_tags = span_tags.O, undersampling:bool = True)->None:
            self._text(d,(x, y_), text=label, font=self._f11, fill=INK, span_tag=span_tags.O)
            fontv = self._f11b if bold else self._f11
            self._text(d,(x + kv_label_w, y_), text=value, font=fontv, fill=INK, span_tag=tag)

        kv_row(left_x, y_left, "Doklad:", "Faktura");
        y_left += mm(5.2)
        kv_row(left_x, y_left, "Datum vystavení:", value=safe(self.issue_date), tag=span_tags.ISSUE_DATE);
        y_left += mm(5.2)
        kv_row(left_x, y_left, "Datum uskuteč. zdan. plnění:", value=safe(self.taxable_supply_date), tag=span_tags.TAXABLE_SUPPLY_DATE);
        y_left += mm(5.2)
        kv_row(left_x, y_left, "Datum splatnosti:", value=safe(self.due_date), tag=span_tags.DUE_DATE);
        y_left += mm(5.2)
        kv_row(left_x, y_left, "Způsob úhrady:", value=safe(self.payment_type), tag=span_tags.PAYMENT_TYPE);
        y_left += mm(5.2)

        self._text(d,(left_x, y_left + mm(2)), text="Bankovní účet:", font=self._f12b, fill=INK)
        y_left += mm(8)
        kv_row(left_x, y_left, label=f"{self.bank_account.name}: ",  value=safe(self.bank_account_number), tag=span_tags.BANK_ACCOUNT_NUMBER);
        y_left += mm(5.2)
        kv_row(left_x, y_left, f"IBAN:", safe(self.IBAN), tag=span_tags.IBAN);
        y_left += mm(5.2)
        kv_row(left_x, y_left, f"BIC:", safe(self.bank_account.BIC), tag=span_tags.BIC);
        y_left += mm(6)
        kv_row(left_x, y_left, "Variabilní symbol:", safe(self.variable_symbol), tag=span_tags.VARIABLE_SYMBOL);
        y_left += mm(8)

        # Pravý blok
        self._text(d,(right_x, y), text="Kupující:", font=self._f12b, fill=INK)
        y_right = y + mm(6)
        d.line([(right_x, y_right), (right_x + col_w, y_right)], fill=LINE_MID, width=2)

        # obsah rámečku
        inner_x = right_x + mm(3)
        y_tmp = y_right + mm(3)

        def kv_r(label:str, value:str, tag: span_tags = span_tags.O, undersampling:bool = True)->None:
            self._text(d,(inner_x, y_tmp), text=label, font=self._f11, fill=INK)
            self._text(d,(inner_x + mm(40), y_tmp), text=safe(value), font=self._f11b, fill=INK, span_tag=tag)

        kv_r("Jméno:", self.customer.name);
        y_tmp += mm(5.2)
        kv_r("Adresa:", self.customer.address);
        y_tmp += mm(5.2)
        kv_r("IČ:", self.customer.register_id, span_tags.CUSTOMER_REGISTER_ID);
        y_tmp += mm(5.2)
        kv_r("DIČ:", self.customer.tax_id, span_tags.CUSTOMER_TAX_ID);
        y_tmp += mm(5.2)

        # posun Y pro další bloky
        y = max(y_left, y_tmp) + mm(4)

        # --- TABULKA POLOŽEK ---
        headers = ["Popis", "Ks", "Cena ks", "bez DPH", "DPH %", "DPH", "Cena s DPH"]
        col_ws = [0.36, 0.08, 0.12, 0.12, 0.08, 0.12, 0.12]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin_l]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        # hlavička
        head_h = mm(7)
        d.rectangle((margin_l, y, margin_l + table_w, y + head_h), outline=None)
        baseline = y + mm(2)
        for i, h in enumerate(headers):
            if i == 0:
                self._text(d,(x_cols[i] + 6, baseline), h, font=self._f11b, fill=INK, must_have_same_width=True)
            elif i in (1, 4):
                self._draw_center(d, x_cols[i] + col_abs[i] / 2, baseline, h, self._f11b, INK, must_have_same_width=True)
            else:
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, baseline, h, self._f11b, INK, must_have_same_width=True)
        y += head_h
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)

        # tělo
        row_h = mm(6.5)
        for it in self.items:
            y += row_h
            # oddělovací linka
            d.line((margin_l, y, margin_l + table_w, y), fill=LINE, width=2)

            cells = [
                safe(it.description),
                safe(it.quantity),
                fmt_money(it.ppu),
                fmt_money(it.price_without_vat),
                f"{safe(it.vat_percentage)}%",
                fmt_money(it.vat),
                fmt_money(it.price_with_vat),
            ]
            # vykreslení buněk
            y_text = y - row_h + mm(2)
            # 0 - popis (vlevo)
            self._text(d,(x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=INK)
            # 1 - ks (střed)
            self._draw_center(d, x_cols[1] + col_abs[1] / 2, y_text, cells[1], self._f11, INK)
            # 2..6 - doprava
            self._draw_right(d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], self._f11, INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], self._f11, INK)
            self._draw_center(d, x_cols[4] + col_abs[4] / 2, y_text, cells[4], self._f11,INK)
            self._draw_right(d, x_cols[5] + col_abs[5] - 6, y_text, cells[5], self._f11, INK)
            self._draw_right(d, x_cols[6] + col_abs[6] - 6, y_text, cells[6], self._f11, INK)

        # tfoot
        y += mm(1.8)
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)
        y += mm(1)
        foot_h = mm(8)

        self._text(d,(margin_l + 6, y + mm(2.5)), "Celkem:", font=self._f11b, fill=INK)
        total_txt = f"{fmt_money(self.calculated_total_price)}"
        self._draw_right(d, margin_l + table_w - 6, y + mm(2.5), total_txt, self._f11b, INK,end=f"{self.currency.value if hasattr(self.currency, 'value') else self.currency}", span_tag=span_tags.TOTAL)
        y += foot_h

        # hr(y, "mid")
        y += mm(2)

        # --- SOUHRNY (DPH vlevo) ---
        box_x = margin_l
        right_summary_w = mm(64)
        gap = mm(10)
        box_w = table_w - right_summary_w - gap
        rows = max(1, len(self.vat))
        box_h = mm(12) + rows * mm(7) + mm(8)

        self._text(d,(box_x + mm(6), y + mm(3)), "Vyčíslení DPH:", font=self._f12b, fill=INK)
        head_y = y + mm(9)
        self._draw_center(d, box_x + box_w * 0.16, head_y, "Sazba", self._f11b, INK)
        self._draw_center(d, box_x + box_w * 0.50, head_y, "Základ", self._f11b,INK)
        self._draw_center(d, box_x + box_w * 0.84, head_y, "DPH", self._f11b, INK)
        d.line((box_x + 4, head_y + mm(4), box_x + box_w - 4, head_y + mm(4)), fill=LINE_STRONG,
                width=3)

        row_y = head_y + mm(6.5)
        for v in self.vat:
            _, percentage_id = self._draw_center(d, box_x + box_w * 0.16, row_y, text=f"{safe(v.vat_percentage)}", end=" %", font=self._f11, fill=INK, span_tag=span_tags.VAT_PERCENTAGE)
            _, base_id = self._draw_right(d, box_x + box_w * 0.66, row_y, fmt_money(v.vat_base), self._f11, INK, span_tag=span_tags.VAT_BASE)
            _, vat_id = self._draw_right(d, box_x + box_w - mm(6), row_y, fmt_money(v.vat), self._f11, INK, span_tag=span_tags.VAT)
            d.line((box_x + 4, row_y + mm(3.5), box_x + box_w - 4, row_y + mm(3.5)), fill=LINE, width=1)
            
            self.append_relationship(GRelationship(None, base_id, percentage_id, relationship_types.BASE_OF))
            self.append_relationship(GRelationship(None, vat_id, percentage_id, relationship_types.VAT_OF))

            row_y += mm(7)

        # Pravý souhrn
        right_block_x = margin_l + box_w + gap
        self._text(d,(right_block_x + mm(25), y + mm(2)),
                f"Zaokrouhlení: {fmt_money(self.rounding)} {self.currency.value if hasattr(self.currency, 'value') else self.currency}",
                font=self._f11, fill=INK)
        self._text(d,(right_block_x + mm(25), y + mm(2) + mm(6)),
                text=f"{fmt_money(self.calculated_total_price)}",
                label="CELKEM: ", end=f" {self.currency.value if hasattr(self.currency, 'value') else self.currency}",font=self._f13b, fill=INK, span_tag=span_tags.TOTAL)

        y = max(y + box_h, y + mm(2) + mm(12))

        hr(y, "thin")
        y += mm(4)

        # --- PATIČKA ---
        self._text(d,(margin_l, y), "Poznámka:", font=self._f11, fill=INK)
        y += mm(10)

        # QR box vpravo
        qr_size = mm(22)
        qr_x = self._A4_W_PX - margin_r - qr_size
        qr_y = y
        d.rectangle((qr_x, qr_y, qr_x + qr_size, qr_y + qr_size), outline=LINE, width=2, fill=None)
        self._draw_center(d, qr_x + qr_size / 2, qr_y + qr_size / 2 - mm(2), "QR", self._f10, (170, 170, 170))

        # Spodní lišta
        bar_y = qr_y + mm(22) + mm(8)
        hr(bar_y, "thin")
        self._text(d,(margin_l, bar_y + mm(2)), "Ochranný znak …", font=self._f11, fill=INK)
        self._draw_center(d, self._A4_W_PX / 2, bar_y + mm(2), "Strana 1 z 1", self._f11, INK)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        self._draw_right(d, self._A4_W_PX - margin_r, bar_y + mm(2), f"Tisk: {now_str}", self._f11, INK)

        # Deformace obrázku
        img = self.post_process(img)
        # img_copy = img.copy()

        #d = ImageDraw.Draw(img)
        # copy_d = ImageDraw.Draw(img_copy)

        #for word in self._spans:
        #    d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #    d.text((word.b_box[0], word.b_box[1]+mm(3)), text=str(word.tag.code), font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        # for word in self._tokens:
        #     copy_d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     copy_d.text((word.b_box[0], word.b_box[1]+mm(3)),word.tag.code, font=self._f10, fill=TMOBILE_PINK)

        # img_copy.show()


        img.save(output_path, format="PNG")

        return True

