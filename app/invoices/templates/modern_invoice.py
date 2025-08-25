from datetime import datetime
import json
import random
from typing import Any, Dict, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

from app.invoices.core.enumerates.banks import banks
from app.invoices.core.invoice import invoice
from app.invoices.utility.json_encoder import json_encoder
from app.invoices.utility.invoice_consts import fonts

@final
class modern_invoice(invoice):
    """Moderní minimalistický design s velkými fonty a čistými liniemi"""
    
    def to_json(self) -> Any:
        data = dict(
            issue_date=self.issue_date, 
            due_date=self.due_date, 
            taxable_supply_date="",
            payment=self.payment.value, 
            bank=self.bank_account, 
            bank_account_number="", 
            IBAN="", 
            variable_symbol=self.variable_symbol, 
            const_symbol="",
            supplier=self.supplier, 
            customer=self.customer,
            items=self.items, 
            vat_items={}, 
            rounding=None,
            total_price=self.calculated_total_price, 
            total_vat=None, 
            currency=self.currency,
            invoice_number=self.invoice_number
        )

        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False))
        
        # Pro moderní fakturu nezobrazujeme telefonní čísla a některé detaily
        j_data["supplier"]["phone"] = ""
        j_data["customer"]["phone"] = ""
        j_data["bank"]["name"] = ""
        j_data["bank"]["code"] = ""
        j_data["bank"]["BIC"] = ""
        
        # Skrýváme detaily položek které se nezobrazují
        for item in j_data["items"]:
            item["vat"] = None

        return j_data

    def generate_img(self, output_path: str) -> bool:
        # Větší okraje pro vzdušnější design
        margin_l = self.mm(20)
        margin_r = self.mm(20)
        margin_t = self.mm(20)
        margin_b = self.mm(20)

        # Světle šedé pozadí
        BG_COLOR = (248, 249, 250)
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG_COLOR)
        d = ImageDraw.Draw(img)

        # Barvy pro moderní design
        PRIMARY_COLOR = (33, 37, 41)
        ACCENT_COLOR = (0, 123, 255)
        LIGHT_GRAY = (108, 117, 125)
        BORDER_COLOR = (206, 212, 218)

        y = margin_t

        # --- HLAVIČKA S BAREVNÝM PRUHEM ---
        header_height = self.mm(25)
        d.rectangle((0, 0, self._A4_W_PX, header_height), fill=ACCENT_COLOR)
        
        # Logo/název vlevo v hlavičce
        d.text((margin_l, margin_t), self._safe(self.supplier.name), font=self._f20b, fill=(255, 255, 255))
        
        # Číslo faktury vpravo
        title_text = f"FAKTURA #{self._safe(self.invoice_number)}"
        self._draw_right(d, self._A4_W_PX - margin_r, margin_t, title_text, self._f20b, (255, 255, 255))

        y = header_height + self.mm(15)

        # --- INFORMACE O FAKTUŘE V BOXECH ---
        box_height = self.mm(35)
        box_width = (self._A4_W_PX - margin_l - margin_r - self.mm(10)) // 2

        # Levý box - dodavatel
        supplier_box = (margin_l, y, margin_l + box_width, y + box_height)
        d.rectangle(supplier_box, fill=(255, 255, 255), outline=BORDER_COLOR, width=2)
        
        d.text((margin_l + self.mm(5), y + self.mm(3)), "DODAVATEL", font=self._f12b, fill=LIGHT_GRAY)
        d.text((margin_l + self.mm(5), y + self.mm(8)), self._safe(self.supplier.name), font=self._f14b, fill=PRIMARY_COLOR)
        d.text((margin_l + self.mm(5), y + self.mm(13)), self._safe(self.supplier.address), font=self._f11, fill=PRIMARY_COLOR)
        d.text((margin_l + self.mm(5), y + self.mm(18)), f"IČ: {self._safe(self.supplier.register_id)}", font=self._f11, fill=PRIMARY_COLOR)
        d.text((margin_l + self.mm(5), y + self.mm(23)), f"DIČ: {self._safe(self.supplier.tax_id)}", font=self._f11, fill=PRIMARY_COLOR)

        # Pravý box - odběratel
        customer_box = (margin_l + box_width + self.mm(10), y, self._A4_W_PX - margin_r, y + box_height)
        d.rectangle(customer_box, fill=(255, 255, 255), outline=BORDER_COLOR, width=2)
        
        customer_x = margin_l + box_width + self.mm(15)
        d.text((customer_x, y + self.mm(3)), "ODBĚRATEL", font=self._f12b, fill=LIGHT_GRAY)
        d.text((customer_x, y + self.mm(8)), self._safe(self.customer.name), font=self._f14b, fill=PRIMARY_COLOR)
        d.text((customer_x, y + self.mm(13)), self._safe(self.customer.address), font=self._f11, fill=PRIMARY_COLOR)
        if self.customer.register_id:
            d.text((customer_x, y + self.mm(18)), f"IČ: {self._safe(self.customer.register_id)}", font=self._f11, fill=PRIMARY_COLOR)
        if self.customer.tax_id:
            d.text((customer_x, y + self.mm(23)), f"DIČ: {self._safe(self.customer.tax_id)}", font=self._f11, fill=PRIMARY_COLOR)

        y += box_height + self.mm(15)

        # --- DETAILY FAKTURY ---
        details_y = y
        d.text((margin_l, details_y), "Datum vystavení:", font=self._f11, fill=LIGHT_GRAY)
        d.text((margin_l + self.mm(35), details_y), self._safe(self.issue_date), font=self._f11b, fill=PRIMARY_COLOR)
        
        d.text((margin_l, details_y + self.mm(6)), "Datum splatnosti:", font=self._f11, fill=LIGHT_GRAY)
        d.text((margin_l + self.mm(35), details_y + self.mm(6)), self._safe(self.due_date), font=self._f11b, fill=PRIMARY_COLOR)

        # Platební údaje vpravo
        payment_x = self._A4_W_PX // 2 + self.mm(10)
        d.text((payment_x, details_y), "Způsob platby:", font=self._f11, fill=LIGHT_GRAY)
        d.text((payment_x + self.mm(30), details_y), self._safe(self.payment.value), font=self._f11b, fill=PRIMARY_COLOR)
        
        d.text((payment_x, details_y + self.mm(6)), "Variabilní symbol:", font=self._f11, fill=LIGHT_GRAY)
        d.text((payment_x + self.mm(30), details_y + self.mm(6)), self._safe(self.variable_symbol), font=self._f11b, fill=PRIMARY_COLOR)

        y += self.mm(20)

        # --- TABULKA POLOŽEK ---
        table_start_y = y
        headers = ["Položka", "Množství", "Cena/ks", "Celkem bez DPH", "DPH%", "Celkem s DPH"]
        col_widths = [0.4, 0.1, 0.15, 0.15, 0.08, 0.12]
        table_width = self._A4_W_PX - margin_l - margin_r
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin_l + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička tabulky
        header_height = self.mm(12)
        d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + header_height), fill=ACCENT_COLOR)
        
        for i, header in enumerate(headers):
            text_x = x_cols[i] + self.mm(3)
            if i > 1:  # Číselné sloupce zarovnáváme doprava
                text_x = x_cols[i] + col_abs[i] - self.mm(3)
                self._draw_right(d, text_x, y + self.mm(3), header, self._f11b, (255, 255, 255))
            else:
                d.text((text_x, y + self.mm(3)), header, font=self._f11b, fill=(255, 255, 255))

        y += header_height

        # Řádky tabulky
        row_height = self.mm(10)
        for i, item in enumerate(self.items):
            # Střídavé pozadí řádků
            bg_color = (255, 255, 255) if i % 2 == 0 else (248, 249, 250)
            d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + row_height), fill=bg_color)
            
            # Obsah řádku
            row_data = [
                self._safe(item.description),
                str(self._safe(item.quantity)),
                self._fmt_money(item.ppu),
                self._fmt_money(item.price_without_vat),
                f"{self._safe(item.vat_percentage)}%",
                self._fmt_money(item.price_with_vat)
            ]
            
            for j, data in enumerate(row_data):
                text_x = x_cols[j] + self.mm(3)
                if j > 1:  # Číselné hodnoty doprava
                    text_x = x_cols[j] + col_abs[j] - self.mm(3)
                    self._draw_right(d, text_x, y + self.mm(2.5), data, self._f10, PRIMARY_COLOR)
                else:
                    d.text((text_x, y + self.mm(2.5)), data, font=self._f10, fill=PRIMARY_COLOR)
            
            y += row_height

        # --- CELKOVÁ ČÁSTKA ---
        y += self.mm(10)
        total_box = (self._A4_W_PX - margin_r - self.mm(60), y, self._A4_W_PX - margin_r, y + self.mm(15))
        d.rectangle(total_box, fill=ACCENT_COLOR)
        
        total_text = f"CELKEM: {self._fmt_money(self.calculated_total_price)} {getattr(self.currency, 'value', self.currency)}"
        self._draw_center(d, total_box[0] + (total_box[2] - total_box[0]) / 2, y + self.mm(4), 
                         total_text, self._f14b, (255, 255, 255))

        # Uložení
        self.post_process(img).save(output_path, format="PNG", quality=100, subsampling=0)
        return True