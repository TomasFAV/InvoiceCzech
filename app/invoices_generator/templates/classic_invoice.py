from datetime import datetime
import json
import random
from typing import Any, Dict, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

import pytesseract

from app.invoices_generator.core.enumerates.banks import banks
from app.invoices_generator.core.enumerates.span_tags import span_tags
from app.invoices_generator.core.invoice import invoice
from app.invoices_generator.utility.json_encoder import json_encoder
from app.invoices_generator.utility.invoice_consts import fonts

@final
class classic_invoice(invoice):
    """Klasická faktura s tradičním layoutem a černobílým designem"""
    
    def to_json_donut(self) -> Any:
        # Plná data pro klasickou fakturu
        data = dict(supplier_name = self.supplier.name, customer_name = self.customer.name,
                    issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date = self.taxable_supply_date,
                    payment=self.payment.value, BIC="", bank_account_number=self.bank_account_number, IBAN=self.IBAN,
                    variable_symbol=self.variable_symbol, const_symbol="",
                    supplier_register_id=self.supplier.register_id, supplier_tax_id=self.supplier.tax_id,
                    customer_register_id=self.customer.register_id, customer_tax_id=self.customer.tax_id,
                    vat_items=[],
                    total_price=self.calculated_total_price, total_vat=None, currency=self.currency,
                    invoice_number=self.invoice_number)

        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False, sort_keys=True))

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
        self._text(d,(margin_l, y), self._safe(self.supplier.name).upper(), font=self._f18b, fill=BLACK)
        
        # Faktura vpravo
        self._draw_right(d, self._A4_W_PX - margin_r, y, label="FAKTURA Č. ", text=f"{self.invoice_number}", font=self._f16b, fill=BLACK, tag=span_tags.INVOICE_NUMBER, undersampling=False)
        
        y += self.mm(12)

        # --- ÚDAJE O FIRMĚ ---
        self._text(d,(margin_l, y), f"Sídlo: {self._safe(self.supplier.address)}", font=self._f10, fill=BLACK)
        y += self.mm(5)
        x_dic, _ = self._text(d,(margin_l, y), label="IČ: ", text=f"{self._safe(self.supplier.register_id)}", end="|", font=self._f10, fill=BLACK, span_tag=span_tags.SUPPLIER_REGISTER_ID, hard_undersampling=False)
        self._text(d,(x_dic, y), label="DIČ: ", text=f"{self._safe(self.supplier.tax_id)}", font=self._f10, fill=BLACK, span_tag=span_tags.SUPPLIER_TAX_ID, hard_undersampling=False)

        y += self.mm(10)
        d.line([(margin_l, y), (self._A4_W_PX - margin_r, y)], fill=LIGHT_GRAY, width=1)
        y += self.mm(8)

        # --- ADRESÁT V RÁMEČKU ---
        box_width = self.mm(80)
        box_height = self.mm(35)
        d.rectangle((margin_l, y, margin_l + box_width, y + box_height), outline=BLACK, width=2)
        
        # Hlavička rámečku
        d.rectangle((margin_l, y, margin_l + box_width, y + self.mm(8)), fill=LIGHT_GRAY)
        self._text(d,(margin_l + self.mm(3), y + self.mm(2)), "FAKTURAČNÍ ADRESA", font=self._f10b, fill=BLACK)
        
        # Obsah
        content_y = y + self.mm(12)
        self._text(d,(margin_l + self.mm(3), content_y), self._safe(self.customer.name), font=self._f11b, fill=BLACK)
        content_y += self.mm(5)
        self._text(d,(margin_l + self.mm(3), content_y), self._safe(self.customer.address), font=self._f10, fill=BLACK)
        content_y += self.mm(5)
        if self.customer.register_id:
            self._text(d,(margin_l + self.mm(3), content_y), label="IČ: ", text=f"{self._safe(self.customer.register_id)}", font=self._f10, fill=BLACK, span_tag=span_tags.CUSTOMER_REGISTER_ID, hard_undersampling=False)
            content_y += self.mm(4)
        if self.customer.tax_id:
            self._text(d,(margin_l + self.mm(3), content_y), label="DIČ: ", text=f"{self._safe(self.customer.tax_id)}", font=self._f10, fill=BLACK, span_tag=span_tags.CUSTOMER_TAX_ID, hard_undersampling=False)

        # --- ÚDAJE O FAKTUŘE VPRAVO ---
        info_x = margin_l + box_width + self.mm(20)
        info_y = y
        
        self._text(d,(info_x, info_y), "ÚDAJE O FAKTUŘE", font=self._f12b, fill=BLACK)
        info_y += self.mm(8)
        
        d.line([(info_x, info_y), (self._A4_W_PX - margin_r, info_y)], fill=BLACK, width=1)
        info_y += self.mm(5)
        
        # Tabulka údajů
        label_width = self.mm(35)
        labels_values = [
            ("Datum vystavení:", self._safe(self.issue_date), span_tags.ISSUE_DATE),
            ("Datum zdaň. plnění:", self._safe(self.taxable_supply_date), span_tags.TAXABLE_SUPPLY_DATE),
            ("Datum splatnosti:", self._safe(self.due_date), span_tags.DUE_DATE),
            ("Způsob úhrady:", self._safe(self.payment.value), span_tags.PAYMENT_TYPE),
            ("Variabilní symbol:", self._safe(self.variable_symbol), span_tags.VARIABLE_SYMBOL),
        ]
        
        for label, value, tag in labels_values:
            self._text(d,(info_x, info_y), label, font=self._f10, fill=BLACK, hard_undersampling=False)
            self._text(d,(info_x + label_width, info_y), value, font=self._f10b, fill=BLACK, span_tag=tag, hard_undersampling=False)
            info_y += self.mm(5)

        y = max(y + box_height + self.mm(15), info_y + self.mm(10))

        # --- TABULKA POLOŽEK ---
        # Hlavička tabulky
        table_y = y
        headers = ["č.", "Popis zboží/služby", "MJ", "Množství", "Cena bez DPH", "DPH %", "Cena s DPH"]
        col_widths = [0.05, 0.25, 0.05, 0.10, 0.25, 0.08, 0.22]
        table_width = self._A4_W_PX - margin_l - margin_r
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin_l + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička s tmavým pozadím
        header_height = self.mm(8)
        d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + header_height), fill=GRAY)
        
        for i, header in enumerate(headers):
            if i in [0, 3,4, 5,6]:  # Číslo, množství, DPH% - střed
                self._draw_center(d, x_cols[i] + col_abs[i] // 2, y + self.mm(2), header, self._f9b, (255, 255, 255))
            else:  # Popis, MJ - vlevo
                self._text(d,(x_cols[i] + self.mm(2), y + self.mm(2)), header, font=self._f9b, fill=(255, 255, 255))

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
                    self._text(d,(x_cols[i] + self.mm(2), text_y), data, font=self._f9, fill=BLACK)
            
            y += row_height

        # Silná linka na konci tabulky
        d.line([(margin_l, y), (self._A4_W_PX - margin_r, y)], fill=BLACK, width=2)
        
        y += self.mm(5)

        # --- REKAPITULACE ---
        # Celková částka v rámečku
        total_box_width = self.mm(50)
        total_box_height = self.mm(12)
        total_x = self._A4_W_PX - margin_r - total_box_width
        
        total_x_end, _ = self._draw_center(d, total_x + total_box_width // 2, y + self.mm(3), label="CELKEM K ÚHRADĚ: ", text=f"{self._fmt_money(self.calculated_total_price)}"
                ,end=f"{self.currency.value}",font=self._f10b, fill=BLACK, tag=span_tags.TOTAL, undersampling=False)

        d.rectangle((total_x, y, total_x_end, y + total_box_height), outline=BLACK, width=2)

        y += total_box_height + self.mm(15)

        # --- PLATEBNÍ ÚDAJE ---
        self._text(d,(margin_l, y), "PLATEBNÍ ÚDAJE", font=self._f12b, fill=BLACK, hard_undersampling=False)
        y += self.mm(6)
        d.line([(margin_l, y), (margin_l + self.mm(40), y)], fill=BLACK, width=1)
        y += self.mm(5)
        
        self._text(d,(margin_l, y), f"Bankovní spojení: {self.bank_account.name}", font=self._f10, fill=BLACK, hard_undersampling=False)
        y += self.mm(4)
        self._text(d,(margin_l, y), label="Číslo účtu: ", text=f"{self._safe(self.bank_account_number)}", font=self._f10, fill=BLACK, span_tag=span_tags.BANK_ACCOUNT_NUMBER, hard_undersampling=False)
        y += self.mm(4)
        self._text(d,(margin_l, y), label="IBAN", text=f"{self._safe(self.IBAN)}", font=self._f10, fill=BLACK, span_tag=span_tags.IBAN, hard_undersampling=False)

        # Uložení
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=self._TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+self.mm(3)),word.tag.value, font=self._f10, fill=self._TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")

        return True