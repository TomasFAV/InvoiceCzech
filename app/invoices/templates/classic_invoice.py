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
class classic_invoice(invoice):
    """Klasická faktura s tradičním layoutem a černobílým designem"""
    
    def to_json(self) -> Any:
        # Plná data pro klasickou fakturu
        data = dict(
            issue_date=self.issue_date, 
            due_date=self.due_date, 
            taxable_supply_date=self.taxable_supply_date,
            payment=self.payment.value, 
            bank=self.bank_account, 
            bank_account_number=self.bank_account_number, 
            IBAN=self.IBAN, 
            variable_symbol=self.variable_symbol, 
            const_symbol="",
            supplier=self.supplier, 
            customer=self.customer,
            items=self.items, 
            vat_items={}, 
            rounding=self.rounding,
            total_price=self.calculated_total_price, 
            total_vat=self.calculated_total_vat, 
            currency=self.currency,
            invoice_number=self.invoice_number
        )

        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False))

        for item in j_data["items"]:
            item["ppu"] = None
            item["vat"] = None

        j_data["bank"]["BIC"] = ""

        return j_data

    def generate_img(self, output_path: str) -> bool:
        # Standardní okraje
        margin_l = self.mm(15)
        margin_r = self.mm(15)
        margin_t = self.mm(15)
        margin_b = self.mm(15)

        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), (255, 255, 255))
        d = ImageDraw.Draw(img)

        # Černobílé barvy
        BLACK = (0, 0, 0)
        GRAY = (128, 128, 128)
        LIGHT_GRAY = (200, 200, 200)

        y = margin_t

        # --- HLAVIČKA ---
        # Dvojitá linie nahoře
        d.line([(margin_l, y), (self._A4_W_PX - margin_r, y)], fill=BLACK, width=3)
        d.line([(margin_l, y + 3), (self._A4_W_PX - margin_r, y + 3)], fill=BLACK, width=1)
        
        y += self.mm(8)
        
        # Název firmy velký font
        d.text((margin_l, y), self._safe(self.supplier.name).upper(), font=self._f18b, fill=BLACK)
        
        # Faktura vpravo
        invoice_text = f"FAKTURA Č. {self._safe(self.invoice_number)}"
        self._draw_right(d, self._A4_W_PX - margin_r, y, invoice_text, self._f16b, BLACK)
        
        y += self.mm(12)

        # --- ÚDAJE O FIRMĚ ---
        d.text((margin_l, y), f"Sídlo: {self._safe(self.supplier.address)}", font=self._f10, fill=BLACK)
        y += self.mm(5)
        d.text((margin_l, y), f"IČ: {self._safe(self.supplier.register_id)} | DIČ: {self._safe(self.supplier.tax_id)}", font=self._f10, fill=BLACK)
        
        y += self.mm(10)
        d.line([(margin_l, y), (self._A4_W_PX - margin_r, y)], fill=LIGHT_GRAY, width=1)
        y += self.mm(8)

        # --- ADRESÁT V RÁMEČKU ---
        box_width = self.mm(80)
        box_height = self.mm(35)
        d.rectangle((margin_l, y, margin_l + box_width, y + box_height), outline=BLACK, width=2)
        
        # Hlavička rámečku
        d.rectangle((margin_l, y, margin_l + box_width, y + self.mm(8)), fill=LIGHT_GRAY)
        d.text((margin_l + self.mm(3), y + self.mm(2)), "FAKTURAČNÍ ADRESA", font=self._f10b, fill=BLACK)
        
        # Obsah
        content_y = y + self.mm(12)
        d.text((margin_l + self.mm(3), content_y), self._safe(self.customer.name), font=self._f11b, fill=BLACK)
        content_y += self.mm(5)
        d.text((margin_l + self.mm(3), content_y), self._safe(self.customer.address), font=self._f10, fill=BLACK)
        content_y += self.mm(5)
        if self.customer.register_id:
            d.text((margin_l + self.mm(3), content_y), f"IČ: {self._safe(self.customer.register_id)}", font=self._f10, fill=BLACK)
            content_y += self.mm(4)
        if self.customer.tax_id:
            d.text((margin_l + self.mm(3), content_y), f"DIČ: {self._safe(self.customer.tax_id)}", font=self._f10, fill=BLACK)

        # --- ÚDAJE O FAKTUŘE VPRAVO ---
        info_x = margin_l + box_width + self.mm(20)
        info_y = y
        
        d.text((info_x, info_y), "ÚDAJE O FAKTUŘE", font=self._f12b, fill=BLACK)
        info_y += self.mm(8)
        
        d.line([(info_x, info_y), (self._A4_W_PX - margin_r, info_y)], fill=BLACK, width=1)
        info_y += self.mm(5)
        
        # Tabulka údajů
        label_width = self.mm(35)
        labels_values = [
            ("Datum vystavení:", self._safe(self.issue_date)),
            ("Datum zdaň. plnění:", self._safe(self.taxable_supply_date)),
            ("Datum splatnosti:", self._safe(self.due_date)),
            ("Způsob úhrady:", self._safe(self.payment.value)),
            ("Variabilní symbol:", self._safe(self.variable_symbol)),
        ]
        
        for label, value in labels_values:
            d.text((info_x, info_y), label, font=self._f10, fill=BLACK)
            d.text((info_x + label_width, info_y), value, font=self._f10b, fill=BLACK)
            info_y += self.mm(5)

        y = max(y + box_height + self.mm(15), info_y + self.mm(10))

        # --- TABULKA POLOŽEK ---
        # Hlavička tabulky
        table_y = y
        headers = ["č.", "Popis zboží/služby", "MJ", "Množství", "Cena bez DPH", "DPH %", "Cena s DPH"]
        col_widths = [0.05, 0.45, 0.08, 0.10, 0.12, 0.08, 0.12]
        table_width = self._A4_W_PX - margin_l - margin_r
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin_l + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička s tmavým pozadím
        header_height = self.mm(8)
        d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + header_height), fill=GRAY)
        
        for i, header in enumerate(headers):
            if i in [0, 3, 5]:  # Číslo, množství, DPH% - střed
                self._draw_center(d, x_cols[i] + col_abs[i] // 2, y + self.mm(2), header, self._f9b, (255, 255, 255))
            elif i in [4, 6]:  # Ceny - doprava
                self._draw_right(d, x_cols[i] + col_abs[i] - self.mm(2), y + self.mm(2), header, self._f9b, (255, 255, 255))
            else:  # Popis, MJ - vlevo
                d.text((x_cols[i] + self.mm(2), y + self.mm(2)), header, font=self._f9b, fill=(255, 255, 255))

        y += header_height

        # Řádky tabulky
        row_height = self.mm(7)
        for idx, item in enumerate(self.items, 1):
            # Ohraničení řádku
            d.line([(margin_l, y + row_height), (self._A4_W_PX - margin_r, y + row_height)], fill=LIGHT_GRAY, width=1)
            
            row_data = [
                str(idx),
                self._safe(item.description),
                "ks",  # jednotka
                str(self._safe(item.quantity)),
                self._fmt_money(item.price_without_vat),
                f"{self._safe(item.vat_percentage)}%",
                self._fmt_money(item.price_with_vat)
            ]
            
            for i, data in enumerate(row_data):
                text_y = y + self.mm(1.5)
                if i in [0, 3, 5]:  # Střed
                    self._draw_center(d, x_cols[i] + col_abs[i] // 2, text_y, data, self._f9, BLACK)
                elif i in [4, 6]:  # Doprava
                    self._draw_right(d, x_cols[i] + col_abs[i] - self.mm(2), text_y, data, self._f9, BLACK)
                else:  # Vlevo
                    d.text((x_cols[i] + self.mm(2), text_y), data, font=self._f9, fill=BLACK)
            
            y += row_height

        # Silná linka na konci tabulky
        d.line([(margin_l, y), (self._A4_W_PX - margin_r, y)], fill=BLACK, width=2)
        
        y += self.mm(5)

        # --- REKAPITULACE ---
        # Celková částka v rámečku
        total_box_width = self.mm(50)
        total_box_height = self.mm(12)
        total_x = self._A4_W_PX - margin_r - total_box_width
        
        d.rectangle((total_x, y, total_x + total_box_width, y + total_box_height), outline=BLACK, width=2)
        
        total_text = f"CELKEM K ÚHRADĚ: {self._fmt_money(self.calculated_total_price)} {getattr(self.currency, 'value', self.currency)}"
        self._draw_center(d, total_x + total_box_width // 2, y + self.mm(3), total_text, self._f10b, BLACK)

        y += total_box_height + self.mm(15)

        # --- PLATEBNÍ ÚDAJE ---
        d.text((margin_l, y), "PLATEBNÍ ÚDAJE", font=self._f12b, fill=BLACK)
        y += self.mm(6)
        d.line([(margin_l, y), (margin_l + self.mm(40), y)], fill=BLACK, width=1)
        y += self.mm(5)
        
        d.text((margin_l, y), f"Bankovní spojení: {self.bank_account.name}", font=self._f10, fill=BLACK)
        y += self.mm(4)
        d.text((margin_l, y), f"Číslo účtu: {self._safe(self.bank_account_number)}", font=self._f10, fill=BLACK)
        y += self.mm(4)
        d.text((margin_l, y), f"IBAN: {self._safe(self.IBAN)}", font=self._f10, fill=BLACK)

        # Uložení
        self.post_process(img).save(output_path, format="PNG", quality=100, subsampling=0)
        return True