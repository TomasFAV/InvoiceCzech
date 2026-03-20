from datetime import datetime
import json
import random
from typing import Any, Dict, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

import pytesseract

from invoices_generator.core.enumerates.banks import banks
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.utility.json_encoder import json_encoder
from invoices_generator.utility.invoice_consts import fonts

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words
from invoices_generator.utility.utils import safe, fmt_money


@final
class modern_invoice(DInvoice):
    """Moderní minimalistický design s velkými fonty a čistými liniemi"""
    

    def generate_img(self, output_path: str) -> bool:
        # Větší okraje pro vzdušnější design
        margin_l = mm(20)
        margin_r = mm(20)
        margin_t = mm(20)
        margin_b = mm(20)

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
        header_height = mm(25)
        d.rectangle((0, 0, self._A4_W_PX, header_height), fill=ACCENT_COLOR)
        
        # Logo/název vlevo v hlavičce
        self._text(d,(margin_l, margin_t), safe(self.supplier.name), font=self._f20b, fill=(255, 255, 255))
        
        # Číslo faktury vpravo
        title_text = f"FAKTURA #{safe(self.invoice_number)}"
        self._draw_right(d, self._A4_W_PX - margin_r, margin_t, label="FAKTURA #", text=f"{safe(self.invoice_number)}", font=self._f20b, fill=(255, 255, 255),
                            span_tag=span_tags.INVOICE_NUMBER)

        y = header_height + mm(15)

        # --- INFORMACE O FAKTUŘE V BOXECH ---
        box_height = mm(35)
        box_width = (self._A4_W_PX - margin_l - margin_r - mm(10)) // 2

        # Levý box - dodavatel
        supplier_box = (margin_l, y, margin_l + box_width, y + box_height)
        d.rectangle(supplier_box, fill=(255, 255, 255), outline=BORDER_COLOR, width=2)
        
        self._text(d,(margin_l + mm(5), y + mm(3)), "DODAVATEL", font=self._f12b, fill=LIGHT_GRAY)
        self._text(d,(margin_l + mm(5), y + mm(8)), safe(self.supplier.name), font=self._f14b, fill=PRIMARY_COLOR)
        self._text(d,(margin_l + mm(5), y + mm(13)), safe(self.supplier.address), font=self._f11, fill=PRIMARY_COLOR)
        self._text(d,(margin_l + mm(5), y + mm(18)), label="IČ: ", text=f"{safe(self.supplier.register_id)}", font=self._f11, fill=PRIMARY_COLOR,
                    span_tag=span_tags.SUPPLIER_REGISTER_ID)
        self._text(d,(margin_l + mm(5), y + mm(23)), label="DIČ: ", text=f"{safe(self.supplier.tax_id)}", font=self._f11, fill=PRIMARY_COLOR, span_tag=span_tags.SUPPLIER_TAX_ID)

        # Pravý box - odběratel
        customer_box = (margin_l + box_width + mm(10), y, self._A4_W_PX - margin_r, y + box_height)
        d.rectangle(customer_box, fill=(255, 255, 255), outline=BORDER_COLOR, width=2)
        
        customer_x = margin_l + box_width + mm(15)
        self._text(d,(customer_x, y + mm(3)), "ODBĚRATEL", font=self._f12b, fill=LIGHT_GRAY)
        self._text(d,(customer_x, y + mm(8)), safe(self.customer.name), font=self._f14b, fill=PRIMARY_COLOR)
        self._text(d,(customer_x, y + mm(13)), safe(self.customer.address), font=self._f11, fill=PRIMARY_COLOR)
        if self.customer.register_id:
            self._text(d,(customer_x, y + mm(18)), label="IČ: ", text=f"{safe(self.customer.register_id)}", font=self._f11, fill=PRIMARY_COLOR,
                        span_tag=span_tags.CUSTOMER_REGISTER_ID)
        if self.customer.tax_id:
            self._text(d,(customer_x, y + mm(23)), label="DIČ:", text= f"{safe(self.customer.tax_id)}", font=self._f11, fill=PRIMARY_COLOR,
                        span_tag=span_tags.CUSTOMER_TAX_ID)

        y += box_height + mm(15)

        # --- DETAILY FAKTURY ---
        details_y = y
        self._text(d,(margin_l, details_y), "Datum vystavení:", font=self._f11, fill=LIGHT_GRAY)
        self._text(d,(margin_l + mm(35), details_y), safe(self.issue_date), font=self._f11b, fill=PRIMARY_COLOR, span_tag=span_tags.ISSUE_DATE)
        
        self._text(d,(margin_l, details_y + mm(6)), "Datum splatnosti:", font=self._f11, fill=LIGHT_GRAY)
        self._text(d,(margin_l + mm(35), details_y + mm(6)), safe(self.due_date), font=self._f11b, fill=PRIMARY_COLOR, span_tag=span_tags.DUE_DATE)

        # Platební údaje vpravo
        payment_x = self._A4_W_PX // 2 + mm(10)
        self._text(d,(payment_x, details_y), "Způsob platby:", font=self._f11, fill=LIGHT_GRAY)
        self._text(d,(payment_x + mm(30), details_y), safe(self.payment_type), font=self._f11b, fill=PRIMARY_COLOR, span_tag=span_tags.PAYMENT_TYPE)
        
        self._text(d,(payment_x, details_y + mm(6)), "Variabilní symbol:", font=self._f11, fill=LIGHT_GRAY)
        self._text(d,(payment_x + mm(30), details_y + mm(6)), safe(self.variable_symbol), font=self._f11b, fill=PRIMARY_COLOR, span_tag=span_tags.VARIABLE_SYMBOL)

        y += mm(20)

        # --- TABULKA POLOŽEK ---
        table_start_y = y
        headers = ["Položka", "Množství", "Cena/ks", "Celkem bez DPH", "DPH%", "Celkem s DPH"]
        col_widths = [0.26, 0.1, 0.15, 0.25, 0.08, 0.16]
        table_width = self._A4_W_PX - margin_l - margin_r
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin_l + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička tabulky
        header_height = mm(12)
        d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + header_height), fill=ACCENT_COLOR)
        
        for i, header in enumerate(headers):
            text_x = x_cols[i] + mm(3)
            if i > 1:  # Číselné sloupce zarovnáváme doprava
                self._draw_center(d,  x_cols[i]+col_abs[i]/2, y + mm(3), header, self._f11b, (255, 255, 255), must_have_same_width=True)
            else:
                self._text(d,(text_x, y + mm(3)), header, font=self._f11b, fill=(255, 255, 255), must_have_same_width=True)

        y += header_height

        # Řádky tabulky
        row_height = mm(10)
        for i, item in enumerate(self.items):
            # Střídavé pozadí řádků
            bg_color = (255, 255, 255) if i % 2 == 0 else (248, 249, 250)
            d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + row_height), fill=bg_color)
            
            # Obsah řádku
            row_data = [
                safe(item.description),
                str(safe(item.quantity)),
                fmt_money(item.ppu),
                fmt_money(item.price_without_vat),
                f"{safe(item.vat_percentage)}%",
                fmt_money(item.price_with_vat)
            ]
            
            for j, data in enumerate(row_data):
                text_x = x_cols[j] + mm(3)
                if j > 1:  # Číselné hodnoty doprava
                    text_x = x_cols[j] + col_abs[j] - mm(3)
                    self._draw_right(d, text_x, y + mm(2.5), data, self._f10, PRIMARY_COLOR)
                else:
                    self._text(d,(text_x, y + mm(2.5)), data, font=self._f10, fill=PRIMARY_COLOR)
            
            y += row_height

        # --- CELKOVÁ ČÁSTKA ---
        y += mm(10)
        total_box = (self._A4_W_PX - margin_r - mm(60), y, self._A4_W_PX - margin_r, y + mm(15))
        d.rectangle(total_box, fill=ACCENT_COLOR)
        
        self._draw_center(d, total_box[0] + (total_box[2] - total_box[0]) / 2, y + mm(4), 
                        label="CELKEM: ", text=f"{fmt_money(self.calculated_total_price)}", end=f"{self.currency.value}", font=self._f14b, fill=(255, 255, 255),
                        span_tag=span_tags.TOTAL, must_have_same_width=True)

        # Uložení
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+mm(3)),word.tag.value, font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")
        return True
