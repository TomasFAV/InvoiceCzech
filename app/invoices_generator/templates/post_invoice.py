from datetime import datetime
import json
from typing import Any, Dict, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

import pytesseract
from app.invoices_generator.core.enumerates.relationship_types import relationship_types
from app.invoices_generator.core.enumerates.span_tags import span_tags
from app.invoices_generator.core.invoice import invoice
from app.invoices_generator.core.relationship import relationship
from app.invoices_generator.utility.json_encoder import json_encoder


@final
class post_invoice(invoice):

    def to_json_donut(self)->Any:
        data = dict(supplier_name = self.supplier.name, customer_name = self.customer.name,
                    issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date = self.taxable_supply_date,
                    payment=self.payment.value, BIC=self.bank_account.BIC, bank_account_number=self.bank_account_number, IBAN=self.IBAN,
                    variable_symbol=self.variable_symbol, const_symbol=self.const_symbol,
                    supplier_register_id=self.supplier.register_id, supplier_tax_id=self.supplier.tax_id,
                    customer_register_id=self.customer.register_id, customer_tax_id=self.customer.tax_id,
                    vat_items=self.vat,
                    total_price=self.calculated_total_price, total_vat=None, currency=self.currency,
                    invoice_number=self.invoice_number)

        #zrušení vazeb na instance bank, zákazníků, dodavatelů
        j_data:Dict[str, Any] = json.loads(json.dumps(data, cls = json_encoder, ensure_ascii=False))

        return j_data


    def generate_img(self, output_path: str) -> bool:
        # Okraje
        margin_l = self.mm(15)
        margin_r = self.mm(15)
        margin_t = self.mm(15)
        margin_b = self.mm(15)

        # Barvy pro ČP design
        _HEADER_BG = (208, 208, 208)
        _CUSTOMER_BG = (232, 232, 232)
        _CUSTOMER_HEADER_BG = (192, 192, 192)
        _TABLE_HEADER_BG = (240, 240, 240)
        _BORDER = (153, 153, 153)

        # Plátno
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        # Start Y
        y = margin_t

        # --- HLAVIČKA S POZADÍM ---
        header_h = self.mm(15)
        d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + header_h),
                    fill=_HEADER_BG, outline=_BORDER, width=2)

        # Text hlavičky
        self._text(d,(margin_l + self.mm(15), y + self.mm(8)), "FAKTURA daňový doklad",
                font=self._f14b, fill=self._INK)

        # Variabilní symbol vpravo
        vs_x = self._A4_W_PX - margin_r - self.mm(15)
        self._draw_right(d, vs_x, y + self.mm(2), "Variabilní symbol pro platbu", self._f10, self._INK, undersampling=False)
        self._draw_right(d, vs_x, y + self.mm(8), self._safe(self.variable_symbol), self._f14b, self._INK, tag=span_tags.VARIABLE_SYMBOL, undersampling=False)

        y += header_h + self.mm(15)

        # --- HLAVNÍ SEKCE DVA SLOUPCE ---
        left_col_w = self.mm(120)
        right_col_w = self.mm(70)
        left_x = margin_l
        right_x = left_x + left_col_w - self.mm(10)

        # LEVÝ SLOUPEC - Dodavatel
        y_left = y

        # Číslo faktury
        self._text(d,(left_x, y_left), label="Č.",text=f"{self._safe(self.invoice_number)}", font=self._f10b, fill=self._INK, span_tag=span_tags.INVOICE_NUMBER, hard_undersampling=False)
        y_left += self.mm(4)
        self._text(d,(left_x, y_left), "- pro účely kontrolního hlášení DPH v ČR",
                font=self._f8, fill=self._INK)
        y_left += self.mm(10)

        # Dodavatel
        self._text(d,(left_x, y_left), "Dodavatel:", font=self._f10b, fill=self._INK)
        #y_left += self.mm(5)

        # Konstantní symbol + ID klienta (pokud máš)
        self._text(d,(left_x+self.mm(50), y_left), label="Konstantní symbol: ", text=f"{self._safe(self.const_symbol)}", font=self._f10b, fill=self._INK,
                    span_tag=span_tags.CONST_SYMBOL, hard_undersampling=False)
        y_left += self.mm(5)

        self._text(d,(left_x, y_left), f"{self._safe(self.supplier.name)} {self._safe(self.supplier.type.value)}, {self._safe(self.supplier.street)}", font=self._f11b, fill=self._INK)
        y_left += self.mm(5)
        self._text(d,(left_x, y_left), f"{self._safe(self.supplier.zip)} {self._safe(self.supplier.city)}", font=self._f10, fill=self._INK)
        y_left += self.mm(5)

        x_supp, _ =self._text(d,(left_x, y_left), label="DIČ: ", text=f"{self._safe(self.supplier.tax_id)}", font=self._f10, fill=self._INK, span_tag=span_tags.SUPPLIER_TAX_ID, hard_undersampling=False)
        self._text(d,(x_supp, y_left), label="IČ: ", text=f"{self._safe(self.supplier.register_id)}", font=self._f10, fill=self._INK, span_tag=span_tags.SUPPLIER_REGISTER_ID, hard_undersampling=False)
        y_left += self.mm(5)



        # Bankovní informace
        # Pokusíme se vytáhnout dostupná pole z self.bank_account
        bank_name = self._safe(self.bank_account.name)
        acc_num = self._safe(getattr(self, "bank_account_number", ""))
        bic = self._safe(getattr(self.bank_account, "BIC", ""))

        
        self._text(d,(left_x, y_left), label=f"IBAN: ", text=f"{self.IBAN}", font=self._f10b, fill=self._INK, span_tag=span_tags.IBAN, hard_undersampling=False)
        y_left += self.mm(5)
        self._text(d,(left_x, y_left), label="SWIFT/BIC: ", text=f"{bic}", font=self._f10b, fill=self._INK, span_tag=span_tags.BIC, hard_undersampling=False)
        y_left += self.mm(15)

        # Dvojice „Peněžní ústav / Číslo účtu“
        self._text(d,(left_x, y_left), "Peněžní ústav:", font=self._f9, fill=self._INK, hard_undersampling=False)
        self._text(d,(left_x + self.mm(50), y_left), "Číslo účtu:", font=self._f9, fill=self._INK, hard_undersampling=False)
        y_left += self.mm(5)
        self._text(d,(left_x, y_left), self._safe(bank_name), font=self._f9, fill=self._INK, hard_undersampling=False)
        self._text(d,(left_x + self.mm(50), y_left), text=self._safe(acc_num), font=self._f9, fill=self._INK, span_tag=span_tags.BANK_ACCOUNT_NUMBER, hard_undersampling=False)
        y_left += self.mm(15)

        # PRAVÝ SLOUPEC - Odběratel
        customer_h = self.mm(50)
        d.rectangle((right_x, y, right_x + right_col_w, y + customer_h),
                    fill=_CUSTOMER_BG, outline=_BORDER, width=2)

        # Hlavička odběratele
        d.rectangle((right_x, y, right_x + right_col_w, y + self.mm(10)),
                    fill=_CUSTOMER_HEADER_BG, outline=_BORDER, width=1)
        self._text(d,(right_x + self.mm(8), y + self.mm(5)), "ODBĚRATEL",
                font=self._f10b, fill=self._INK)

        # Údaje odběratele
        customer_y = y + self.mm(12)
        self._text(d,(right_x + self.mm(3), customer_y), self._safe(self.customer.name),
                font=self._f12b, fill=self._INK)
        customer_y += self.mm(8)
        self._text(d,(right_x + self.mm(3), customer_y), self._safe(self.customer.address),
                font=self._f10, fill=self._INK)
        customer_y += self.mm(8)
        x_cust, _ = self._text(d,(right_x + self.mm(3), customer_y),
                label="IČ:", text=f"{self._safe(self.customer.register_id)}", end=",",
                font=self._f10, fill=self._INK, span_tag=span_tags.CUSTOMER_REGISTER_ID, hard_undersampling=False)
        self._text(d,(x_cust, customer_y),
                label="DIČ:", text=f"{self._safe(self.customer.tax_id)}", end=",",
                font=self._f10, fill=self._INK, span_tag=span_tags.CUSTOMER_TAX_ID, hard_undersampling=False)
        

        # QR kód placeholder (případně sem můžeš vygenerovat skutečný QR)
        qr_size = self.mm(15)
        qr_x = right_x + right_col_w - self.mm(20)
        qr_y = y + customer_h + self.mm(5)
        d.rectangle((qr_x, qr_y, qr_x + qr_size, qr_y + qr_size),
                    fill=(240, 240, 240), outline=_BORDER, width=2)
        self._draw_center(d, qr_x + qr_size/2, qr_y + qr_size/2 - self.mm(2),
                        "QR", self._f8, (102, 102, 102))

        y += customer_h + self.mm(30)

        # --- DATUMY A ÚDAJE ---
        dates_h = self.mm(25)
        table_w = self._A4_W_PX - margin_l - margin_r

        pay_str = self._safe(self.payment.value) if hasattr(self.payment, "value") else self._safe(self.payment)
        curr_str = self.currency.value if hasattr(self.currency, "value") else str(self.currency)

        dates_data = [
            ("Datum vystavení daňového dokladu", self._safe(self.issue_date), "Den splatnosti", self._safe(self.due_date), span_tags.ISSUE_DATE, span_tags.DUE_DATE),
            ("Datum uskutečnění zdanitelného plnění", self._safe(self.taxable_supply_date), "Forma úhrady", pay_str, span_tags.TAXABLE_SUPPLY_DATE, span_tags.PAYMENT_TYPE),
            ("", "", "Měna", curr_str, span_tags.O, span_tags.O)
        ]

        for i, (label1, val1, label2, val2, tag1, tag2) in enumerate(dates_data):
            row_y = y + i * self.mm(8)
            d.line([(margin_l, row_y + self.mm(6)), (self._A4_W_PX - margin_r, row_y + self.mm(6))],
                    fill=(204, 204, 204), width=1)

            if label1:
                self._text(d,(margin_l, row_y), label1, font=self._f10b, fill=self._INK, hard_undersampling=False)
                self._text(d,(margin_l + self.mm(70), row_y), self._safe(val1), font=self._f10b, fill=self._INK, span_tag=tag1, hard_undersampling=False)

            if label2:
                self._text(d,(margin_l + self.mm(105), row_y), label2, font=self._f10b, fill=self._INK, hard_undersampling=False)
                self._text(d,(margin_l + self.mm(140), row_y), self._safe(val2), font=self._f10b, fill=self._INK, span_tag=tag2, hard_undersampling=False)

        y += dates_h + self.mm(10)

        # --- TABULKA POLOŽEK ---
        headers = ["Pol.", "Množství", "Předmět plnění", "Sazba DPH", "Celkem"]
        col_widths = [0.08, 0.20, 0.37, 0.15, 0.20]
        col_abs = [int(w * table_w) for w in col_widths]
        x_cols = [margin_l]
        for w in col_abs[:-1]:
            x_cols.append(x_cols[-1] + w)

        header_h = self.mm(12)
        d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + header_h),
                    fill=_TABLE_HEADER_BG, outline=_BORDER, width=2)

        # Svislé čáry hlavičky
        for x in x_cols[1:]:
            d.line([(x, y), (x, y + header_h)], fill=_BORDER, width=2)

        # Texty hlavičky
        for i, header in enumerate(headers):
            self._draw_center(d, x_cols[i] + col_abs[i]/2, y + self.mm(5), header, self._f10b, self._INK)

        y += header_h

        # Řádky položek (dynamicky)
        row_h = self.mm(7)
        for idx, it in enumerate(self.items, start=1):
            d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + row_h),
                        fill=self._BG, outline=_BORDER, width=2)

            # Svislé čáry
            for x in x_cols[1:]:
                d.line([(x, y), (x, y + row_h)], fill=_BORDER, width=2)

            qty_unit = ""
            if hasattr(it, "quantity"):
                unit = getattr(it, "unit", "ks")
                qty_unit = f"{self._safe(it.quantity)} {self._safe(unit)}"

            # Buňky
            self._draw_center(d, x_cols[0] + col_abs[0]/2, y + self.mm(2), f"{idx:03}", self._f9, self._INK)  # Pol.
            self._draw_center(d, x_cols[1] + col_abs[1]/2, y + self.mm(2), qty_unit, self._f9, self._INK)     # Množství
            self._text(d,(x_cols[2] + self.mm(2), y + self.mm(1)), self._safe(it.description), font=self._f9, fill=self._INK)  # Popis
            self._draw_center(d, x_cols[3] + col_abs[3]/2, y + self.mm(2), f"{self._safe(it.vat_percentage)} %", self._f9, self._INK)  # DPH %
            self._draw_right(d, x_cols[4] + col_abs[4] - self.mm(3), y + self.mm(2), self._fmt_money(it.price_with_vat), self._f9, self._INK)  # Celkem

            y += row_h

        y += self.mm(10)

        # --- SOUHRN DPH ---
        summary_h = self.mm(7)
        summary_headers = ["Sazba DPH %", "Základ DPH", "DPH", "Celkem s DPH"]
        summary_widths = [0.20, 0.25, 0.20, 0.25]
        summary_abs = [int(w * table_w) for w in summary_widths]
        summary_x_cols = [margin_l]
        for w in summary_abs[:-1]:
            summary_x_cols.append(summary_x_cols[-1] + w)

        # Hlavička souhrnu
        d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + summary_h),
                    fill=_TABLE_HEADER_BG, outline=_BORDER, width=2)

        for x in summary_x_cols[1:]:
            d.line([(x, y), (x, y + summary_h)], fill=_BORDER, width=2)

        for i, header in enumerate(summary_headers):
            self._draw_center(d, summary_x_cols[i] + summary_abs[i]/2, y + self.mm(3), header, self._f10b, self._INK, undersampling=False)

        y += summary_h

        # Data souhrnu (dle self.vat)
        for v in self.vat:
            d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + summary_h),
                        fill=self._BG, outline=_BORDER, width=2)
            for x in summary_x_cols[1:]:
                d.line([(x, y), (x, y + summary_h)], fill=_BORDER, width=2)

            _, percentage_id = self._draw_center(d, summary_x_cols[0] + summary_abs[0]/2, y + self.mm(2),
                            f"{self._safe(v.vat_percentage)}", self._f10, self._INK, tag=span_tags.VAT_PERCENTAGE, undersampling=False)
            _, base_id = self._draw_right(d, summary_x_cols[1] + summary_abs[1] - self.mm(3), y + self.mm(2),
                            self._fmt_money(v.vat_base), self._f10, self._INK, tag=span_tags.VAT_BASE, undersampling=False)
            _, vat_id = self._draw_right(d, summary_x_cols[2] + summary_abs[2] - self.mm(3), y + self.mm(2),
                            self._fmt_money(v.vat), self._f10, self._INK, tag=span_tags.VAT, undersampling=False)
            self._draw_right(d, summary_x_cols[3] + summary_abs[3] - self.mm(3), y + self.mm(2),
                            self._fmt_money(v.vat_base + v.vat), self._f10, self._INK)
            

            self._relationships.append(relationship(base_id, percentage_id, relationship_types.BASE_OF))
            self._relationships.append(relationship(vat_id, percentage_id, relationship_types.VAT_OF))
            
            y += summary_h

        y += self.mm(5)

        # --- CELKOVÉ ČÁSTKY ---
        d.line([(margin_l, y), (self._A4_W_PX - margin_r, y)], fill=self._LINE_STRONG, width=2)
        y += self.mm(3)

        self._text(d,(margin_l, y), "Celkem", font=self._f12b, fill=self._INK, hard_undersampling=False)
        self._draw_right(d, self._A4_W_PX - margin_r, y, text=self._fmt_money(self.calculated_total_price), font=self._f12b, fill=self._INK, tag=span_tags.TOTAL, undersampling=False)
        y += self.mm(8)

        d.line([(margin_l, y), (self._A4_W_PX - margin_r, y)], fill=self._LINE_STRONG, width=2)
        y += self.mm(3)

        self._text(d,(margin_l, y), "Celkem k úhradě", font=self._f12b, fill=self._INK, hard_undersampling=False)
        self._draw_right(
            d,
            self._A4_W_PX - margin_r,
            y,
            text=f"{self._fmt_money(self.calculated_total_price)}",
            font=self._f12b,
            fill=self._INK,
            tag=span_tags.TOTAL,
            undersampling=False
        )


        #img.show()
        # Uložení
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=self._TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+self.mm(3)),word.tag.value, font=self._f10, fill=self._TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")

        return True
