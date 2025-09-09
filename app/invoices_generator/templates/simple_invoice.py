from datetime import datetime
import json
from typing import Any, Dict, Optional, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

import pytesseract
from app.invoices_generator.core.enumerates.relationship_types import relationship_types
from app.invoices_generator.core.enumerates.span_tags import span_tags
from app.invoices_generator.core.invoice import invoice
from app.invoices_generator.core.relationship import relationship
from app.invoices_generator.utility.json_encoder import json_encoder

@final
class simple_invoice(invoice):

    def to_json_donut(self) -> Any:
        data = dict(supplier_name = self.supplier.name, customer_name = self.customer.name,
                    issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date = "",
                    payment=self.payment.value, BIC="", bank_account_number=self.bank_account_number, IBAN=self.IBAN,
                    variable_symbol=self.variable_symbol, const_symbol="",
                    supplier_register_id=self.supplier.register_id, supplier_tax_id=self.supplier.tax_id,
                    customer_register_id=self.customer.register_id, customer_tax_id=self.customer.tax_id,
                    vat_items=self.vat,
                    total_price=self.calculated_total_price, total_vat=None, currency=self.currency,
                    invoice_number=self.invoice_number)

        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False, sort_keys=True))

        return j_data

    def generate_img(self, output_path: str) -> bool:
        margin_l = self.mm(20)
        margin_r = self.mm(20)
        margin_t = self.mm(20)
        
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            color = self._LINE_MID if weight == "mid" else (self._LINE_STRONG if weight == "strong" else self._LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        y = margin_t

        # --- ZÁVĚREČNÁ SUMA Nahoře ---
        total_price_x = self._A4_W_PX - margin_r - self.mm(40)
        self._text(d,(total_price_x, y), "CELKEM K ZAPLACENÍ", font=self._f13b, fill=self._INK, hard_undersampling=False)
        y += self.mm(5)
        self._text(d,(total_price_x, y), text=f"{self._fmt_money(self.calculated_total_price)}", end=f"{self.currency.value}", font=self._f17b, fill=self._INK, span_tag=span_tags.TOTAL, 
                    hard_undersampling=False)
        
        # Datové pole uprostřed nahoře
        date_box_x = self._A4_W_PX / 2
        
        self._draw_center(d, date_box_x, margin_t, "FAKTURA", self._f17b, self._INK, undersampling=False)
        self._draw_center(d, date_box_x, margin_t + self.mm(8), label=f"Číslo faktury: ", text=f"{self._safe(self.invoice_number)}", font=self._f13b, fill=self._INK,
                            tag=span_tags.INVOICE_NUMBER, undersampling=False)
        
        y += self.mm(15)
        hr(y, "strong")
        y += self.mm(5)
        
        # --- BLOKY INFORMACÍ PROHOZENÉ ---
        # Bankovní účet a symboly - Nalevo
        bank_x = margin_l
        self._text(d,(bank_x, y), "Platební údaje:", font=self._f12b, fill=self._INK, hard_undersampling=False)
        y += self.mm(5)
        self._text(d,(bank_x, y), label="Bankovní účet:", text=f"{self._safe(self.bank_account_number)}", font=self._f11, fill=self._INK, span_tag=span_tags.BANK_ACCOUNT_NUMBER, hard_undersampling=False)
        y += self.mm(5)
        self._text(d,(bank_x, y), label="IBAN: ", text=f"{self._safe(self.IBAN)}", font=self._f11, fill=self._INK, span_tag=span_tags.IBAN, hard_undersampling=False)
        y += self.mm(5)
        self._text(d,(bank_x, y), label="Variabilní symbol: ", text=f"{self._safe(self.variable_symbol)}", font=self._f11b, fill=self._INK, span_tag=span_tags.VARIABLE_SYMBOL, hard_undersampling=False)

        # Datové pole - Napravo
        dates_x = self._A4_W_PX - margin_r - self.mm(50)
        self._text(d,(dates_x, y - self.mm(15)), "Datum vystavení:", font=self._f11, fill=self._INK, hard_undersampling=False)
        self._text(d,(dates_x + self.mm(30), y - self.mm(15)), self._safe(self.issue_date), font=self._f11b, fill=self._INK, span_tag=span_tags.ISSUE_DATE, hard_undersampling=False)
        
        self._text(d,(dates_x, y - self.mm(10)), "Datum splatnosti:", font=self._f11, fill=self._INK, hard_undersampling=False)
        self._text(d,(dates_x + self.mm(30), y - self.mm(10)), self._safe(self.due_date), font=self._f11b, fill=self._INK, span_tag=span_tags.DUE_DATE, hard_undersampling=False)
        
        self._text(d,(dates_x, y - self.mm(5)), "Způsob platby:", font=self._f11, fill=self._INK, hard_undersampling=False)
        self._text(d,(dates_x + self.mm(30), y - self.mm(5)), self._safe(self.payment.value), font=self._f11b, fill=self._INK, span_tag=span_tags.PAYMENT_TYPE, hard_undersampling=False)

        # --- DODAVATEL / ODBĚRATEL VE STŘEDU ---
        y_middle = y + self.mm(5)
        
        # Dodavatel
        self._draw_center(d, self._A4_W_PX / 2, y_middle, "DODAVATEL", self._f12b, self._INK)
        self._draw_center(d, self._A4_W_PX / 2, y_middle + self.mm(5), self._safe(self.supplier.name), self._f11b, self._INK)
        self._draw_center(d, self._A4_W_PX / 2, y_middle + self.mm(10), self._safe(self.supplier.address), self._f11, self._INK)
        x_end, _ = self._draw_center(d, self._A4_W_PX / 2, y_middle + self.mm(15), label=f"IČ: ", text=f"{self._safe(self.supplier.register_id)}", font=self._f11, fill=self._INK, tag=span_tags.SUPPLIER_REGISTER_ID, undersampling=False)
        self._text(d, (x_end, y_middle + self.mm(15)), label=f"DIČ: ", text=f"{self._safe(self.supplier.tax_id)}", font=self._f11, fill=self._INK, span_tag=span_tags.SUPPLIER_TAX_ID, hard_undersampling=False)
        y = y_middle + self.mm(25)
        
        # Odběratel
        self._draw_center(d, self._A4_W_PX / 2, y, "ODBĚRATEL", self._f12b, self._INK)
        self._draw_center(d, self._A4_W_PX / 2, y + self.mm(5), self._safe(self.customer.name), self._f11b, self._INK)
        self._draw_center(d, self._A4_W_PX / 2, y + self.mm(10), self._safe(self.customer.address), self._f11, self._INK)       
        x_end, _ = self._draw_center(d, self._A4_W_PX / 2, y + self.mm(15), label=f"IČ: ", text=f"{self._safe(self.customer.register_id)}", font=self._f11, fill=self._INK, tag=span_tags.CUSTOMER_REGISTER_ID, undersampling=False)
        self._text(d, (x_end, y + self.mm(15)), label=f"DIČ: ", text=f"{self._safe(self.customer.tax_id)}", font=self._f11, fill=self._INK, span_tag=span_tags.CUSTOMER_TAX_ID, hard_undersampling=False)

        y += self.mm(25)
        hr(y, "strong")
        y += self.mm(5)
        
        # --- TABULKA POLOŽEK ---
        table_w = self._A4_W_PX - 2 * margin_l
        headers = ["Popis zboží", "Cena ks bez DPH", "DPH %", "Celkem s DPH"]
        col_ws = [0.45, 0.20, 0.15, 0.20]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin_l]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        head_h = self.mm(7)
        baseline = y + self.mm(2)
        
        for i, h in enumerate(headers):
            if i == 0:
                self._text(d,(x_cols[i] + 6, baseline), h, font=self._f11b, fill=self._INK)
            else:
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, baseline, h, self._f11b, self._INK)
        
        y += head_h
        d.line((margin_l, y, margin_l + table_w, y), fill=self._LINE_STRONG, width=2)
        
        row_h = self.mm(6.5)
        for it in self.items:
            y += row_h
            d.line((margin_l, y, margin_l + table_w, y), fill=self._LINE, width=1)
            
            cells = [
                f"{self._safe(it.quantity)}x {self._safe(it.description)}",
                self._fmt_money(it.ppu),
                f"{self._safe(it.vat_percentage)}%",
                self._fmt_money(it.price_with_vat),
            ]
            
            y_text = y - row_h + self.mm(2)
            self._text(d,(x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=self._INK)
            self._draw_right(d, x_cols[1] + col_abs[1] - 6, y_text, cells[1], self._f11, self._INK)
            self._draw_right(d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], self._f11, self._INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], self._f11, self._INK)

        y += self.mm(2)
        hr(y, "strong")
        y += self.mm(5)

        # --- PATIČKA ---
        
        # QR Kód a poznámky - dole
        qr_size = self.mm(20)
        qr_x = self.mm(20)
        qr_y = self._A4_H_PX - self.mm(40)
        d.rectangle((qr_x, qr_y, qr_x + qr_size, qr_y + qr_size), outline=self._LINE, width=2, fill=None)
        self._draw_center(d, qr_x + qr_size / 2, qr_y + qr_size / 2, "QR", self._f10, (170, 170, 170))
        
        self._text(d,(qr_x + qr_size + self.mm(5), qr_y), "Děkujeme za Váš nákup.", font=self._f11, fill=self._INK)
        self._text(d,(qr_x + qr_size + self.mm(5), qr_y + self.mm(5)), "Faktura byla vygenerována automaticky.", font=self._f10, fill=self._INK)
        
        # Souhrny DPH - vpravo dole
        vat_summary_x = self._A4_W_PX - margin_r - self.mm(80)
        y_vat = self._A4_H_PX - self.mm(35)
        self._text(d,(vat_summary_x, y_vat), "Souhrn DPH:", font=self._f11b, fill=self._INK, hard_undersampling=False)
        y_vat += self.mm(5)
        for v in self.vat:
            x_end, percentage_id = self._text(d,(vat_summary_x, y_vat), label="Sazba", text=f"{self._safe(v.vat_percentage)}", end="%",font=self._f10, fill=self._INK, span_tag=span_tags.VAT_PERCENTAGE, 
                                                hard_undersampling=False)
            x_end, base_id = self._text(d,(x_end, y_vat), label="Základ", text=f"{self._safe(v.vat_base)}", font=self._f10, fill=self._INK, span_tag=span_tags.VAT_BASE, hard_undersampling=False)
            x_end, vat_id = self._text(d,(x_end, y_vat), label="DPH", text=f"{self._safe(v.vat)}",font=self._f10, fill=self._INK, span_tag=span_tags.VAT, hard_undersampling=False)
            y_vat += self.mm(4)

            self._relationships.append(relationship(base_id, percentage_id, relationship_types.BASE_OF))
            self._relationships.append(relationship(vat_id, percentage_id, relationship_types.VAT_OF))

        hr(self._A4_H_PX - self.mm(15), "strong")
        
        self._draw_center(d, self._A4_W_PX / 2, self._A4_H_PX - self.mm(12), "Strana 1 z 1", self._f10, self._INK)
        self._text(d,(self._A4_W_PX - margin_r, self._A4_H_PX - self.mm(12)), f"Tisk: {datetime.now().strftime('%d.%m.%Y %H:%M')}", font=self._f10, fill=self._INK)

        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=self._TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+self.mm(3)),word.tag.value, font=self._f10, fill=self._TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")

        return True