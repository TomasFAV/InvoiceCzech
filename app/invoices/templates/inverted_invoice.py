from datetime import datetime
import json
from typing import Any, Dict, Optional, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

from app.invoices.core.invoice import invoice
from app.invoices.utility.json_encoder import json_encoder

@final
class inverted_invoice(invoice):

    def to_json(self) -> Any:
        data = dict(issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date=self.taxable_supply_date,
                    payment=self.payment.value, bank=self.bank_account, bank_account_number="", IBAN="",
                    variable_symbol=self.variable_symbol, const_symbol="",
                    supplier=self.supplier, customer=self.customer,
                    items=self.items, vat_items=self.vat, rounding=self.rounding,
                    total_price=self.calculated_total_price, total_vat=self.calculated_total_vat, currency=self.currency,
                    invoice_number=self.invoice_number)

        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False))

        if "supplier" in j_data and "phone" in j_data["supplier"]:
            j_data["supplier"]["phone"] = ""
        if "customer" in j_data and "phone" in j_data["customer"]:
            j_data["customer"]["phone"] = ""

        for item in j_data["items"]:
            item["price_without_vat"] = None
            item["vat"] = None
            item["vat_percentage"] = None


        j_data["bank"]["name"] = ""
        j_data["bank"]["BIC"] = ""
        j_data["bank"]["code"] = ""

        return j_data

    def generate_img(self, output_path: str) -> bool:
        margin = self.mm(25)
        
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        # --- HLAVIČKA A INFO O FAKTUŘE ---
        y = margin
        d.text((margin, y), f"Faktura / Daňový doklad č. {self._safe(self.invoice_number)}", font=self._f17b, fill=self._INK)
        
        y += self.mm(10)
        d.text((margin, y), f"Datum vystavení: {self._safe(self.issue_date)}", font=self._f11, fill=self._INK)
        d.text((margin, y + self.mm(5)), f"Datum splatnosti: {self._safe(self.due_date)}", font=self._f11, fill=self._INK)
        d.text((margin, y + self.mm(10)), f"Způsob úhrady: {self._safe(self.payment.value)}", font=self._f11, fill=self._INK)
        d.text((margin, y + self.mm(15)), f"Variabilní symbol: {self._safe(self.variable_symbol)}", font=self._f11b, fill=self._INK)

        # Adresy v bloku vpravo
        address_block_x = self._A4_W_PX - margin - self.mm(80)
        y_address = margin
        d.text((address_block_x, y_address), "DODAVATEL:", font=self._f12b, fill=self._INK)
        y_address += self.mm(6)
        d.text((address_block_x, y_address), self._safe(self.supplier.name), font=self._f11b, fill=self._INK)
        y_address += self.mm(5)
        d.text((address_block_x, y_address), self._safe(self.supplier.address), font=self._f11, fill=self._INK)
        y_address += self.mm(5)
        d.text((address_block_x, y_address), f"IČ: {self._safe(self.supplier.register_id)} | DIČ: {self._safe(self.supplier.tax_id)}", font=self._f11, fill=self._INK)
        
        y_address += self.mm(10)
        d.text((address_block_x, y_address), "ODBĚRATEL:", font=self._f12b, fill=self._INK)
        y_address += self.mm(6)
        d.text((address_block_x, y_address), self._safe(self.customer.name), font=self._f11b, fill=self._INK)
        y_address += self.mm(5)
        d.text((address_block_x, y_address), self._safe(self.customer.address), font=self._f11, fill=self._INK)
        y_address += self.mm(5)
        d.text((address_block_x, y_address), f"IČ: {self._safe(self.customer.register_id)} | DIČ: {self._safe(self.customer.tax_id)}", font=self._f11, fill=self._INK)

        y = max(y + self.mm(25), y_address + self.mm(10))

        # --- SOUHRN DPH NAD TABULKOU ---
        y += self.mm(10)
        
        # Levé zarovnání souhrnu
        summary_x = margin
        d.text((summary_x, y), "Přehled DPH:", font=self._f12b, fill=self._INK)
        y += self.mm(5)
        
        for v in self.vat:
            vat_line = f"Sazba {self._safe(v.vat_percentage)}%: Základ {self._fmt_money(v.vat_base)} | DPH {self._fmt_money(v.vat)}"
            d.text((summary_x, y), vat_line, font=self._f11, fill=self._INK)
            y += self.mm(5)

        y += self.mm(5)
        d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=self._LINE_STRONG, width=2)
        y += self.mm(5)

        # --- TABULKA POLOŽEK ---
        table_w = self._A4_W_PX - 2 * margin
        
        headers = ["Popis zboží/služby", "Ks", "Jednotková cena", "Celkem"]
        col_ws = [0.4, 0.1, 0.25, 0.25]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        head_h = self.mm(7)
        baseline = y + self.mm(2)
        for i, h in enumerate(headers):
            if i == 0:
                d.text((x_cols[i] + 6, baseline), h, font=self._f11b, fill=self._INK)
            else:
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, baseline, h, self._f11b, fill=self._INK)
        
        y += head_h
        d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=self._LINE_STRONG, width=2)
        
        row_h = self.mm(6.5)
        for it in self.items:
            y += row_h
            d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=self._LINE, width=1)
            
            cells = [
                self._safe(it.description),
                self._safe(it.quantity),
                self._fmt_money(it.ppu),
                self._fmt_money(it.price_with_vat),
            ]
            
            y_text = y - row_h + self.mm(2)
            d.text((x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=self._INK)
            self._draw_right(d, x_cols[1] + col_abs[1] - 6, y_text, cells[1], self._f11, fill=self._INK)
            self._draw_right(d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], self._f11, fill=self._INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], self._f11, fill=self._INK)

        y += self.mm(5)
        
        # --- CELKOVÁ SUMA V PRAVÉM DOLNÍM ROHU ---
        total_box_x = self._A4_W_PX - margin - self.mm(70)
        total_box_w = self.mm(70)
        y_total = y + self.mm(10)
        
        d.text((total_box_x, y_total), "Celkem k úhradě:", font=self._f13b, fill=self._INK)
        self._draw_right(d, total_box_x + total_box_w, y_total, f"{self._fmt_money(self.calculated_total_price)} {self.currency.value}", font=self._f13b, fill=self._INK)

        # --- PATIČKA ---
        footer_y = self._A4_H_PX - self.mm(30)
        d.line([(margin, footer_y), (self._A4_W_PX - margin, footer_y)], fill=self._LINE_STRONG, width=2)
        footer_y += self.mm(5)
        
        d.text((margin, footer_y), "Platbu prosím proveďte na výše uvedený bankovní účet.", font=self._f11, fill=self._INK)
        self._draw_right(d, self._A4_W_PX - margin, footer_y, f"Datum tisku: {datetime.now().strftime('%d.%m.%Y')}", font=self._f11, fill=self._INK)
        
        self.post_process(img).save(output_path, format="PNG", quality=100, subsampling=0)
        return True