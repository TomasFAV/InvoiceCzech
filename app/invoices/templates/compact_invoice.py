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
class compact_invoice(invoice):
    """Kompaktní faktura s hustším layoutem a menšími fonty"""
    
    def to_json(self) -> Any:
        # Minimální set dat pro kompaktní fakturu
        data = dict(issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date="",
                    payment=self.payment.value, bank=self.bank_account, bank_account_number=self.bank_account_number, IBAN = self.IBAN, 
                    variable_symbol=self.variable_symbol, const_symbol="", 
                    supplier = self.supplier, customer = self.customer,
                    items = self.items, vat_items = self.vat, rounding = self.rounding,
                    total_price = self.calculated_total_price, total_vat = None, currency = self.currency,
                    invoice_number = self.invoice_number)

        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False))
        
        # Omezujeme zobrazovaná data
        j_data["supplier"]["phone"] = ""
        j_data["customer"]["phone"] = ""
        j_data["bank"]["name"] = ""
        j_data["bank"]["BIC"] = ""

        for item in j_data["items"]:
            item["vat"] = None
            item["vat_percentage"] = None
            item["price_without_vat"] = None


        

        return j_data

    def generate_img(self, output_path: str) -> bool:
        # Menší okraje pro kompaktní design
        margin = self.mm(10)
        
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), (255, 255, 255))
        d = ImageDraw.Draw(img)

        DARK_BLUE = (25, 42, 86)
        LIGHT_BLUE = (74, 144, 226)
        GRAY = (95, 99, 104)

        y = margin

        # --- KOMPAKTNÍ HLAVIČKA ---
        # Barevný pruh nahoře
        d.rectangle((0, 0, self._A4_W_PX, self.mm(6)), fill=DARK_BLUE)
        
        y += self.mm(8)
        
        # Informace v jednom řádku
        d.text((margin, y), f"{self._safe(self.supplier.name)} | FAKTURA {self._safe(self.invoice_number)}", 
               font=self._f14b, fill=DARK_BLUE)
        
        # Datum vpravo
        self._draw_right(d, self._A4_W_PX - margin, y, f"Datum: {self._safe(self.issue_date)}", 
                        self._f12, GRAY)
        
        y += self.mm(12)

        # --- ÚDAJE VE DVOU SLOUPCÍCH ---
        col_width = (self._A4_W_PX - 2 * margin - self.mm(10)) // 2
        
        # Levý sloupec - dodavatel
        d.text((margin, y), "DODAVATEL", font=self._f10b, fill=LIGHT_BLUE)
        y += self.mm(4)
        d.text((margin, y), self._safe(self.supplier.name), font=self._f11b, fill=DARK_BLUE)
        y += self.mm(4)
        d.text((margin, y), self._safe(self.supplier.address), font=self._f9, fill=GRAY)
        y += self.mm(3)
        d.text((margin, y), f"IČ: {self._safe(self.supplier.register_id)} | DIČ: {self._safe(self.supplier.tax_id)}", 
               font=self._f9, fill=GRAY)

        # Pravý sloupec - odběratel
        customer_x = margin + col_width + self.mm(10)
        customer_y = y - self.mm(11)  # Začínáme na stejné výši
        
        d.text((customer_x, customer_y), "ODBĚRATEL", font=self._f10b, fill=LIGHT_BLUE)
        customer_y += self.mm(4)
        d.text((customer_x, customer_y), self._safe(self.customer.name), font=self._f11b, fill=DARK_BLUE)
        customer_y += self.mm(4)
        d.text((customer_x, customer_y), self._safe(self.customer.address), font=self._f9, fill=GRAY)
        customer_y += self.mm(3)
        if self.customer.register_id:
            d.text((customer_x, customer_y), f"IČ: {self._safe(self.customer.register_id)}", font=self._f9, fill=GRAY)

        y += self.mm(15)

        # --- PLATEBNÍ INFO V ŘÁDKU ---
        payment_info = f"Splatnost: {self._safe(self.due_date)} | Platba: {self._safe(self.payment.value)} | VS: {self._safe(self.variable_symbol)}"
        d.text((margin, y), payment_info, font=self._f10, fill=GRAY)
        
        y += self.mm(10)
        
        # Tenká linka
        d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=LIGHT_BLUE, width=1)
        y += self.mm(8)

        # --- KOMPAKTNÍ TABULKA ---
        headers = ["Položka", "Ks", "Cena", "Celkem"]
        col_widths = [0.6, 0.1, 0.15, 0.15]
        table_width = self._A4_W_PX - 2 * margin
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička tabulky
        header_height = self.mm(8)
        for i, header in enumerate(headers):
            if i == 0:  # Položka vlevo
                d.text((x_cols[i] + self.mm(2), y), header, font=self._f10b, fill=DARK_BLUE)
            elif i == 1:  # Ks na střed
                self._draw_center(d, x_cols[i] + col_abs[i] // 2, y, header, self._f10b, DARK_BLUE)
            else:  # Ceny doprava
                self._draw_right(d, x_cols[i] + col_abs[i] - self.mm(2), y, header, self._f10b, DARK_BLUE)

        y += header_height
        d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=DARK_BLUE, width=2)

        # Řádky položek
        row_height = self.mm(6)
        for item in self.items:
            y += row_height
            
            # Obsah řádku
            d.text((x_cols[0] + self.mm(2), y - self.mm(4)), self._safe(item.description)[:40], font=self._f9, fill=DARK_BLUE)
            
            self._draw_center(d, x_cols[1] + col_abs[1] // 2, y - self.mm(4), 
                            str(self._safe(item.quantity)), self._f9, DARK_BLUE)
            
            self._draw_right(d, x_cols[2] + col_abs[2] - self.mm(2), y - self.mm(4), 
                           self._fmt_money(item.ppu), self._f9, DARK_BLUE)
            
            self._draw_right(d, x_cols[3] + col_abs[3] - self.mm(2), y - self.mm(4), 
                           self._fmt_money(item.price_with_vat), self._f9, DARK_BLUE)
            
            # Tenká linka
            d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=(220, 220, 220), width=1)

        # Celkova suma
        y += self.mm(5)
        d.rectangle((x_cols[2], y, self._A4_W_PX - margin, y + self.mm(10)), fill=DARK_BLUE)
        
        total_text = f"CELKEM: {self._fmt_money(self.calculated_total_price)} {getattr(self.currency, 'value', self.currency)}"
        self._draw_right(d, self._A4_W_PX - margin - self.mm(2), y + self.mm(2.5), 
                        total_text, self._f11b, (255, 255, 255))

        y += self.mm(20)

        # --- PLATEBNÍ ÚDAJE V PATIČCE ---
        d.text((margin, y), f"Číslo účtu: {self._safe(self.bank_account_number)}", font=self._f9, fill=GRAY)

        # Uložení
        self.post_process(img).save(output_path, format="PNG", quality=100, subsampling=0)
        return True