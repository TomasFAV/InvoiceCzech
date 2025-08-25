from datetime import datetime
import json
from typing import Any, Dict, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

from app.invoices.core.invoice import invoice
from app.invoices.utility.json_encoder import json_encoder


@final
class post_invoice(invoice):

    def to_json(self)->Any:

        data:Dict[str, Any] = dict(issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date=self.taxable_supply_date,
                    payment=self.payment.value, bank=self.bank_account, bank_account_number=self.bank_account_number, IBAN = self.IBAN, 
                    variable_symbol=self.variable_symbol, const_symbol=self.const_symbol, 
                    supplier = self.supplier, customer = self.customer,
                    items = self.items, vat_items = self.vat, rounding = self.rounding,
                    total_price = self.calculated_total_price, total_vat = self.calculated_total_vat, currency = self.currency,
                    invoice_number = self.invoice_number)

        #zrušení vazeb na instance bank, zákazníků, dodavatelů
        j_data:Dict[str, Any] = json.loads(json.dumps(data, cls = json_encoder, ensure_ascii=False))

        #Mazání informací, které nejsou z faktury dostupné
        j_data["total_vat"] = None
        j_data["customer"]["phone"] = ""
        j_data["supplier"]["phone"] = ""
        j_data["rounding"] = None

        for item in j_data["items"]:
            item["vat"] = None
            item["ppu"] = None
            item["price_without_vat"] = None

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
        d.text((margin_l + self.mm(15), y + self.mm(8)), "FAKTURA daňový doklad",
               font=self._f14b, fill=self._INK)

        # Variabilní symbol vpravo
        vs_x = self._A4_W_PX - margin_r - self.mm(15)
        self._draw_right(d, vs_x, y + self.mm(2), "Variabilní symbol pro platbu", self._f10, self._INK)
        self._draw_right(d, vs_x, y + self.mm(8), self._safe(self.variable_symbol), self._f14b, self._INK)

        y += header_h + self.mm(15)

        # --- HLAVNÍ SEKCE DVA SLOUPCE ---
        left_col_w = self.mm(120)
        right_col_w = self.mm(70)
        left_x = margin_l
        right_x = left_x + left_col_w - self.mm(10)

        # LEVÝ SLOUPEC - Dodavatel
        y_left = y

        # Číslo faktury
        d.text((left_x, y_left), f"Č.{self._safe(self.invoice_number)}", font=self._f10b, fill=self._INK)
        y_left += self.mm(4)
        d.text((left_x, y_left), "- pro účely kontrolního hlášení DPH v ČR",
               font=self._f8, fill=self._INK)
        y_left += self.mm(10)

        # Dodavatel
        d.text((left_x, y_left), "Dodavatel:", font=self._f10b, fill=self._INK)
        #y_left += self.mm(5)

        # Konstantní symbol + ID klienta (pokud máš)
        d.text((left_x+self.mm(50), y_left), f"Konstantní symbol: {self._safe(self.const_symbol)}", font=self._f10b, fill=self._INK)
        y_left += self.mm(5)

        d.text((left_x, y_left), f"{self._safe(self.supplier.name)} {self._safe(self.supplier.type.value)}, {self._safe(self.supplier.street)}", font=self._f11b, fill=self._INK)
        y_left += self.mm(5)
        d.text((left_x, y_left), f"{self._safe(self.supplier.zip)} {self._safe(self.supplier.city)}", font=self._f10, fill=self._INK)
        y_left += self.mm(5)

        d.text((left_x, y_left),
               f"DIČ: {self._safe(self.supplier.tax_id)}      IČ: {self._safe(self.supplier.register_id)}",
               font=self._f10, fill=self._INK)
        y_left += self.mm(5)

        # Bankovní informace
        # Pokusíme se vytáhnout dostupná pole z self.bank_account
        bank_name = self._safe(self.bank_account.name)
        acc_num = self._safe(getattr(self, "bank_account_number", ""))
        iban = self._safe(getattr(self, "IBAN", ""))
        bic = self._safe(getattr(self.bank_account, "BIC", ""))

        if iban:
            d.text((left_x, y_left), f"IBAN: {iban}", font=self._f10b, fill=self._INK)
            y_left += self.mm(5)
        if bic:
            d.text((left_x, y_left), f"SWIFT/BIC: {bic}", font=self._f10b, fill=self._INK)
            y_left += self.mm(15)

        # Dvojice „Peněžní ústav / Číslo účtu“
        d.text((left_x, y_left), "Peněžní ústav:", font=self._f9, fill=self._INK)
        d.text((left_x + self.mm(50), y_left), "Číslo účtu:", font=self._f9, fill=self._INK)
        y_left += self.mm(5)
        d.text((left_x, y_left), self._safe(bank_name), font=self._f9, fill=self._INK)
        d.text((left_x + self.mm(50), y_left), self._safe(acc_num), font=self._f9, fill=self._INK)
        y_left += self.mm(15)

        # PRAVÝ SLOUPEC - Odběratel
        customer_h = self.mm(50)
        d.rectangle((right_x, y, right_x + right_col_w, y + customer_h),
                    fill=_CUSTOMER_BG, outline=_BORDER, width=2)

        # Hlavička odběratele
        d.rectangle((right_x, y, right_x + right_col_w, y + self.mm(10)),
                    fill=_CUSTOMER_HEADER_BG, outline=_BORDER, width=1)
        d.text((right_x + self.mm(8), y + self.mm(5)), "ODBĚRATEL",
               font=self._f10b, fill=self._INK)

        # Údaje odběratele
        customer_y = y + self.mm(12)
        d.text((right_x + self.mm(3), customer_y), self._safe(self.customer.name),
               font=self._f12b, fill=self._INK)
        customer_y += self.mm(8)
        d.text((right_x + self.mm(3), customer_y), self._safe(self.customer.address),
               font=self._f10, fill=self._INK)
        customer_y += self.mm(8)
        d.text((right_x + self.mm(3), customer_y),
               f"IČ: {self._safe(self.customer.register_id)}, DIČ: {self._safe(self.customer.tax_id)}",
               font=self._f10, fill=self._INK)

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
            ("Datum vystavení daňového dokladu", self._safe(self.issue_date), "Den splatnosti", self._safe(self.due_date)),
            ("Datum uskutečnění zdanitelného plnění", self._safe(self.taxable_supply_date), "Forma úhrady", pay_str),
            ("", "", "Měna", curr_str)
        ]

        for i, (label1, val1, label2, val2) in enumerate(dates_data):
            row_y = y + i * self.mm(8)
            d.line([(margin_l, row_y + self.mm(6)), (self._A4_W_PX - margin_r, row_y + self.mm(6))],
                   fill=(204, 204, 204), width=1)

            if label1:
                d.text((margin_l, row_y), label1, font=self._f10b, fill=self._INK)
                d.text((margin_l + self.mm(70), row_y), self._safe(val1), font=self._f10b, fill=self._INK)

            if label2:
                d.text((margin_l + self.mm(105), row_y), label2, font=self._f10b, fill=self._INK)
                d.text((margin_l + self.mm(140), row_y), self._safe(val2), font=self._f10b, fill=self._INK)

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
            d.text((x_cols[2] + self.mm(2), y + self.mm(1)), self._safe(it.description), font=self._f9, fill=self._INK)  # Popis
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
            self._draw_center(d, summary_x_cols[i] + summary_abs[i]/2, y + self.mm(3), header, self._f10b, self._INK)

        y += summary_h

        # Data souhrnu (dle self.vat)
        for v in self.vat:
            d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + summary_h),
                        fill=self._BG, outline=_BORDER, width=2)
            for x in summary_x_cols[1:]:
                d.line([(x, y), (x, y + summary_h)], fill=_BORDER, width=2)

            self._draw_center(d, summary_x_cols[0] + summary_abs[0]/2, y + self.mm(2),
                              f"{self._safe(v.vat_percentage)}", self._f10, self._INK)
            self._draw_right(d, summary_x_cols[1] + summary_abs[1] - self.mm(3), y + self.mm(2),
                             self._fmt_money(v.vat_base), self._f10, self._INK)
            self._draw_right(d, summary_x_cols[2] + summary_abs[2] - self.mm(3), y + self.mm(2),
                             self._fmt_money(v.vat), self._f10, self._INK)
            self._draw_right(d, summary_x_cols[3] + summary_abs[3] - self.mm(3), y + self.mm(2),
                             self._fmt_money(v.vat_base + v.vat), self._f10, self._INK)
            y += summary_h

        y += self.mm(5)

        # --- CELKOVÉ ČÁSTKY ---
        d.line([(margin_l, y), (self._A4_W_PX - margin_r, y)], fill=self._LINE_STRONG, width=2)
        y += self.mm(3)

        d.text((margin_l, y), "Celkem", font=self._f12b, fill=self._INK)
        self._draw_right(d, self._A4_W_PX - margin_r, y, self._fmt_money(self.calculated_total_price), self._f12b, self._INK)
        y += self.mm(8)

        d.line([(margin_l, y), (self._A4_W_PX - margin_r, y)], fill=self._LINE_STRONG, width=2)
        y += self.mm(3)

        d.text((margin_l, y), "Celkem k úhradě", font=self._f12b, fill=self._INK)
        self._draw_right(
            d,
            self._A4_W_PX - margin_r,
            y,
            f"{self._fmt_money(self.calculated_total_price)}",
            self._f12b,
            self._INK
        )


        #img.show()
        # Uložení
        self.post_process(img).save(output_path, format="PNG", quality=100, subsampling=0)
        return True
