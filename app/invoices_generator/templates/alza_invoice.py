from datetime import datetime
import json
import random
from typing import Any, Dict, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

import pytesseract

from app.invoices_generator.core.enumerates.banks import banks
from app.invoices_generator.core.enumerates.relationship_types import relationship_types
from app.invoices_generator.core.enumerates.span_tags import span_tags
from app.invoices_generator.core.invoice import invoice
from app.invoices_generator.core.relationship import relationship
from app.invoices_generator.utility.json_encoder import json_encoder
from app.invoices_generator.utility.invoice_consts import fonts
from app.ie_engine.enumerates.engines import engines

@final
class alza_invoice(invoice):

    def to_json_donut(self)->str:
        #Mazání informací, které nejsou z faktury dostupné
        data = dict(supplier_name = self.supplier.name, customer_name = self.customer.name,
                    issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date = self.taxable_supply_date,
                    payment=self.payment.value, BIC=self.bank_account.BIC, bank_account_number=self.bank_account_number, IBAN=self.IBAN,
                    variable_symbol=self.variable_symbol, const_symbol="",
                    supplier_register_id=self.supplier.register_id, supplier_tax_id=self.supplier.tax_id,
                    customer_register_id=self.customer.register_id, customer_tax_id=self.customer.tax_id,
                    vat_items=self.vat,
                    total_price=self.calculated_total_price, total_vat=None, currency=self.currency,
                    invoice_number=self.invoice_number)

        #zrušení vazeb na instance bank, zákazníků, dodavatelů
        j_data:Dict[str, Any] = json.loads(json.dumps(data, cls = json_encoder, ensure_ascii=False, method="to_json_donut"))

        return j_data

    def generate_img(self, output_path: str) -> bool:
        # Okraje (podle .page padding)
        margin_l = self.mm(14)
        margin_r = self.mm(14)
        margin_t = self.mm(12)
        margin_b = self.mm(14)

        # Plátno
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        # Pomocné čáry
        def hr(y:int, weight:str="mid", x0:int|None=None, x1:int|None=None)->None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            color = self._LINE_MID if weight == "mid" else (self._LINE_STRONG if weight == "strong" else self._LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        # Start Y
        y = margin_t

        # --- HLAVIČKA ---
        # Logo/jméno dodavatele vlevo
        self._text(d,(margin_l, y), text=self._safe(self.supplier.name), font=self._f16b, fill=self._INK)

        # Titul (centrovaný blok vpravo části)
        title_center_x = self._A4_W_PX // 2
        self._draw_center(d, title_center_x, y, text=f"{self._safe(self.invoice_number)}", font=self._f17b, fill=self._INK, label="Faktura - Daňový doklad -", tag=span_tags.INVOICE_NUMBER, undersampling=False)
        self._draw_center(d, title_center_x, y + self.mm(12), "záruční a dodací list -", self._f12, self._MUTED)

        y += self.mm(18)
        local_x = margin_l
        # --- Prodávající ---
        self._text(d,(margin_l, y), text=f"Prodávající: {self._safe(self.supplier.name)} {self.supplier.type.value}", font=self._f12b,
                fill=self._INK)
        
        y += self.mm(5.2)
        local_x, _ = self._text(d,(local_x, y),
                text=f"{self._safe(self.supplier.address)},",
                font=self._f11, fill=self._INK)
        
        local_x, _ = self._text(d,(local_x, y),
                text=f"{self._safe(self.supplier.register_id)}",
                font=self._f11, fill=self._INK, span_tag=span_tags.SUPPLIER_REGISTER_ID, label="IČ: ", end=",", hard_undersampling=False)

        local_x, _ = self._text(d,(local_x, y),
                text=f"{self._safe(self.supplier.tax_id)}",
                font=self._f11, fill=self._INK, span_tag=span_tags.SUPPLIER_TAX_ID, label="DIČ: ", end=",", hard_undersampling=False)
        

        local_x, _ = self._text(d,(local_x, y),
                text=f"internet: www.{self._safe(self.supplier.name)}.cz, kontakt: www.{self._safe(self.supplier.name)}.cz/kontakt",
                font=self._f11, fill=self._INK)

        y += self.mm(4)

        y += self.mm(1.5)

        # --- Dva sloupce ---
        col_gap = self.mm(24)
        table_w = self._A4_W_PX - margin_l - margin_r
        col_w = (table_w - col_gap) // 2
        left_x = margin_l
        right_x = margin_l + col_w + col_gap

        # Levý blok
        self._text(d,(left_x, y), text="Daňový doklad:", font=self._f12b, fill=self._INK)
        y_left = y + self.mm(6)

        kv_label_w = self.mm(60)

        def kv_row(x:int, y_:int, label:str, value:str, bold:bool=True, tag: span_tags = span_tags.O, undersampling:bool = True)->None:
            self._text(d,(x, y_), text=label, font=self._f11, fill=self._INK, span_tag=span_tags.O, hard_undersampling=undersampling)
            fontv = self._f11b if bold else self._f11
            self._text(d,(x + kv_label_w, y_), text=value, font=fontv, fill=self._INK, span_tag=tag, hard_undersampling=undersampling)

        kv_row(left_x, y_left, "Doklad:", "Faktura");
        y_left += self.mm(5.2)
        kv_row(left_x, y_left, "Datum vystavení:", value=self._safe(self.issue_date), tag=span_tags.ISSUE_DATE, undersampling=False);
        y_left += self.mm(5.2)
        kv_row(left_x, y_left, "Datum uskuteč. zdan. plnění:", value=self._safe(self.taxable_supply_date), tag=span_tags.TAXABLE_SUPPLY_DATE, undersampling=False);
        y_left += self.mm(5.2)
        kv_row(left_x, y_left, "Datum splatnosti:", value=self._safe(self.due_date), tag=span_tags.DUE_DATE, undersampling=False);
        y_left += self.mm(5.2)
        kv_row(left_x, y_left, "Způsob úhrady:", value=self._safe(self.payment.value), tag=span_tags.PAYMENT_TYPE, undersampling=False);
        y_left += self.mm(5.2)

        self._text(d,(left_x, y_left + self.mm(2)), text="Bankovní účet:", font=self._f12b, fill=self._INK, hard_undersampling=False)
        y_left += self.mm(8)
        kv_row(left_x, y_left, label=f"{self.bank_account.name}: ",  value=self._safe(self.bank_account_number), tag=span_tags.BANK_ACCOUNT_NUMBER, undersampling=False);
        y_left += self.mm(5.2)
        kv_row(left_x, y_left, f"IBAN:", self._safe(self.IBAN), tag=span_tags.IBAN, undersampling=False);
        y_left += self.mm(5.2)
        kv_row(left_x, y_left, f"BIC:", self._safe(self.bank_account.BIC), tag=span_tags.BIC, undersampling=False);
        y_left += self.mm(6)
        kv_row(left_x, y_left, "Variabilní symbol:", self._safe(self.variable_symbol), tag=span_tags.VARIABLE_SYMBOL, undersampling=False);
        y_left += self.mm(8)

        # Pravý blok
        self._text(d,(right_x, y), text="Kupující:", font=self._f12b, fill=self._INK)
        y_right = y + self.mm(6)
        d.line([(right_x, y_right), (right_x + col_w, y_right)], fill=self._LINE_MID, width=2)

        # obsah rámečku
        inner_x = right_x + self.mm(3)
        y_tmp = y_right + self.mm(3)

        def kv_r(label:str, value:str, tag: span_tags = span_tags.O, undersampling:bool = True)->None:
            self._text(d,(inner_x, y_tmp), text=label, font=self._f11, fill=self._INK, hard_undersampling=undersampling)
            self._text(d,(inner_x + self.mm(30), y_tmp), text=self._safe(value), font=self._f11b, fill=self._INK, span_tag=tag, hard_undersampling=undersampling)

        kv_r("Jméno:", self.customer.name);
        y_tmp += self.mm(5.2)
        kv_r("Adresa:", self.customer.address);
        y_tmp += self.mm(5.2)
        kv_r("IČ:", self.customer.register_id, span_tags.CUSTOMER_REGISTER_ID, undersampling=False);
        y_tmp += self.mm(5.2)
        kv_r("DIČ:", self.customer.tax_id, span_tags.CUSTOMER_TAX_ID, undersampling=False);
        y_tmp += self.mm(5.2)

        # posun Y pro další bloky
        y = max(y_left, y_tmp) + self.mm(4)

        # --- TABULKA POLOŽEK ---
        headers = ["Popis", "Ks", "Cena ks", "bez DPH", "DPH %", "DPH", "Cena s DPH"]
        col_ws = [0.36, 0.08, 0.12, 0.12, 0.08, 0.12, 0.12]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin_l]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        # hlavička
        head_h = self.mm(7)
        d.rectangle((margin_l, y, margin_l + table_w, y + head_h), outline=None)
        baseline = y + self.mm(2)
        for i, h in enumerate(headers):
            if i == 0:
                self._text(d,(x_cols[i] + 6, baseline), h, font=self._f11b, fill=self._INK)
            elif i in (1, 4):
                self._draw_center(d, x_cols[i] + col_abs[i] / 2, baseline, h, self._f11b, self._INK)
            else:
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, baseline, h, self._f11b, self._INK)
        y += head_h
        d.line((margin_l, y, margin_l + table_w, y), fill=self._LINE_STRONG, width=2)

        # tělo
        row_h = self.mm(6.5)
        for it in self.items:
            y += row_h
            # oddělovací linka
            d.line((margin_l, y, margin_l + table_w, y), fill=self._LINE, width=2)

            cells = [
                self._safe(it.description),
                self._safe(it.quantity),
                self._fmt_money(it.ppu),
                self._fmt_money(it.price_without_vat),
                f"{self._safe(it.vat_percentage)}%",
                self._fmt_money(it.vat),
                self._fmt_money(it.price_with_vat),
            ]
            # vykreslení buněk
            y_text = y - row_h + self.mm(2)
            # 0 - popis (vlevo)
            self._text(d,(x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=self._INK)
            # 1 - ks (střed)
            self._draw_center(d, x_cols[1] + col_abs[1] / 2, y_text, cells[1], self._f11, self._INK)
            # 2..6 - doprava
            self._draw_right(d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], self._f11, self._INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], self._f11, self._INK)
            self._draw_center(d, x_cols[4] + col_abs[4] / 2, y_text, cells[4], self._f11, self._INK)
            self._draw_right(d, x_cols[5] + col_abs[5] - 6, y_text, cells[5], self._f11, self._INK)
            self._draw_right(d, x_cols[6] + col_abs[6] - 6, y_text, cells[6], self._f11, self._INK)

        # tfoot
        y += self.mm(1.8)
        d.line((margin_l, y, margin_l + table_w, y), fill=self._LINE_STRONG, width=2)
        y += self.mm(1)
        foot_h = self.mm(8)

        self._text(d,(margin_l + 6, y + self.mm(2.5)), "Celkem:", font=self._f11b, fill=self._INK, hard_undersampling=False)
        total_txt = f"{self._fmt_money(self.calculated_total_price)} {self.currency.value if hasattr(self.currency, 'value') else self.currency}"
        self._draw_right(d, margin_l + table_w - 6, y + self.mm(2.5), total_txt, self._f11b, self._INK, undersampling=False)
        y += foot_h

        # hr(y, "mid")
        y += self.mm(2)

        # --- SOUHRNY (DPH vlevo) ---
        box_x = margin_l
        right_summary_w = self.mm(64)
        gap = self.mm(10)
        box_w = table_w - right_summary_w - gap
        rows = max(1, len(self.vat))
        box_h = self.mm(12) + rows * self.mm(7) + self.mm(8)

        self._text(d,(box_x + self.mm(6), y + self.mm(3)), "Vyčíslení DPH:", font=self._f12b, fill=self._INK, hard_undersampling=False)
        head_y = y + self.mm(9)
        self._draw_center(d, box_x + box_w * 0.16, head_y, "Sazba", self._f11b, self._INK, undersampling=False)
        self._draw_center(d, box_x + box_w * 0.50, head_y, "Základ", self._f11b, self._INK, undersampling=False)
        self._draw_center(d, box_x + box_w * 0.84, head_y, "DPH", self._f11b, self._INK, undersampling=False)
        d.line((box_x + 4, head_y + self.mm(4), box_x + box_w - 4, head_y + self.mm(4)), fill=self._LINE_STRONG,
                width=3)

        row_y = head_y + self.mm(6.5)
        for v in self.vat:
            _, percentage_id = self._draw_center(d, box_x + box_w * 0.16, row_y, text=f"{self._safe(v.vat_percentage)}", end=" %", font=self._f11, fill=self._INK, tag=span_tags.VAT_PERCENTAGE, undersampling=False)
            _, base_id = self._draw_right(d, box_x + box_w * 0.66, row_y, self._fmt_money(v.vat_base), self._f11, self._INK, tag=span_tags.VAT_BASE, undersampling=False)
            _, vat_id = self._draw_right(d, box_x + box_w - self.mm(6), row_y, self._fmt_money(v.vat), self._f11, self._INK, tag=span_tags.VAT, undersampling=False)
            d.line((box_x + 4, row_y + self.mm(3.5), box_x + box_w - 4, row_y + self.mm(3.5)), fill=self._LINE, width=1)
            
            self._relationships.append(relationship(base_id, percentage_id, relationship_types.BASE_OF))
            self._relationships.append(relationship(vat_id, percentage_id, relationship_types.VAT_OF))

            row_y += self.mm(7)

        # Pravý souhrn
        right_block_x = margin_l + box_w + gap
        self._text(d,(right_block_x + self.mm(25), y + self.mm(2)),
                f"Zaokrouhlení: {self._fmt_money(self.rounding)} {self.currency.value if hasattr(self.currency, 'value') else self.currency}",
                font=self._f11, fill=self._INK, hard_undersampling=False)
        self._text(d,(right_block_x + self.mm(25), y + self.mm(2) + self.mm(6)),
                text=f"{self._fmt_money(self.calculated_total_price)}",
                label="CELKEM: ", end=f" {self.currency.value if hasattr(self.currency, 'value') else self.currency}",font=self._f13b, fill=self._INK, span_tag=span_tags.TOTAL, hard_undersampling=False)

        y = max(y + box_h, y + self.mm(2) + self.mm(12))

        hr(y, "thin")
        y += self.mm(4)

        # --- PATIČKA ---
        self._text(d,(margin_l, y), "Poznámka:", font=self._f11, fill=self._INK)
        y += self.mm(10)

        # QR box vpravo
        qr_size = self.mm(22)
        qr_x = self._A4_W_PX - margin_r - qr_size
        qr_y = y
        d.rectangle((qr_x, qr_y, qr_x + qr_size, qr_y + qr_size), outline=self._LINE, width=2, fill=None)
        self._draw_center(d, qr_x + qr_size / 2, qr_y + qr_size / 2 - self.mm(2), "QR", self._f10, (170, 170, 170))

        # Spodní lišta
        bar_y = qr_y + self.mm(22) + self.mm(8)
        hr(bar_y, "thin")
        self._text(d,(margin_l, bar_y + self.mm(2)), "Ochranný znak …", font=self._f11, fill=self._INK)
        self._draw_center(d, self._A4_W_PX / 2, bar_y + self.mm(2), "Strana 1 z 1", self._f11, self._INK)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        self._draw_right(d, self._A4_W_PX - margin_r, bar_y + self.mm(2), f"Tisk: {now_str}", self._f11, self._INK)

        # Deformace obrázku
        img = self.post_process(img)
        # img_copy = img.copy()

        # d = ImageDraw.Draw(img)
        # copy_d = ImageDraw.Draw(img_copy)

        # for word in self._spans:
        #     d.rectangle(word.b_box, outline=self._TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+self.mm(3)),word.tag.code, font=self._f10, fill=self._TMOBILE_PINK)

        # img.show()

        # for word in self._tokens:
        #     copy_d.rectangle(word.b_box, outline=self._TMOBILE_PINK)
        #     copy_d.text((word.b_box[0], word.b_box[1]+self.mm(3)),word.tag.code, font=self._f10, fill=self._TMOBILE_PINK)

        # img_copy.show()


        img.save(output_path, format="PNG")

        return True

