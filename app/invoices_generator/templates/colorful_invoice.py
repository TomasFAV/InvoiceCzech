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
class colorful_invoice(invoice):
    """Barevná faktura s gradientem a moderními prvky"""
    
    def to_json_donut(self) -> Any:
        data = dict(supplier_name = self.supplier.name, customer_name = self.customer.name,
                    issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date="",
                    payment="", BIC="", bank_account_number="", IBAN="",
                    variable_symbol=self.variable_symbol, const_symbol=self.const_symbol,
                    supplier_register_id=self.supplier.register_id, supplier_tax_id=self.supplier.tax_id,
                    customer_register_id=self.customer.register_id, customer_tax_id=self.customer.tax_id,
                    vat_items=[],
                    total_price=self.calculated_total_price, total_vat=None, currency=self.currency,
                    invoice_number=self.invoice_number)

        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False, sort_keys=True))

        return j_data

    def generate_img(self, output_path: str) -> bool:
        margin_l = self.mm(18)
        margin_r = self.mm(18)  
        margin_t = self.mm(15)
        margin_b = self.mm(15)

        # Světlé pozadí s nádechem barvy
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), (250, 251, 255))
        d = ImageDraw.Draw(img)

        # Barevná paleta
        PRIMARY = (138, 43, 226)  # Fialová
        SECONDARY = (255, 105, 180)  # Růžová
        ACCENT = (30, 144, 255)  # Modrá
        DARK = (33, 37, 41)
        LIGHT_GRAY = (248, 249, 250)

        y = margin_t

        # --- BAREVNÁ HLAVIČKA S GRADIENTEM ---
        header_height = self.mm(30)
        
        # Simulace gradientu pomocí více obdélníků
        gradient_steps = 20
        for i in range(gradient_steps):
            step_height = header_height // gradient_steps
            # Interpolace mezi PRIMARY a SECONDARY
            ratio = i / gradient_steps
            r = int(PRIMARY[0] * (1 - ratio) + SECONDARY[0] * ratio)
            g = int(PRIMARY[1] * (1 - ratio) + SECONDARY[1] * ratio)
            b = int(PRIMARY[2] * (1 - ratio) + SECONDARY[2] * ratio)
            
            d.rectangle((0, i * step_height, self._A4_W_PX, (i + 1) * step_height), fill=(r, g, b))

        # Text v hlavičce
        self._text(d,(margin_l, margin_t + self.mm(5)), self._safe(self.supplier.name), 
                    font=self._f20b, fill=(255, 255, 255))
        
        # Číslo faktury stylizované
        invoice_bg = (255, 255, 255, 180)  # Poloprůhledné pozadí
        self._draw_right(d, self._A4_W_PX - margin_r, margin_t, 
                        label="INVOICE #", text=f"{self._safe(self.invoice_number)}", font=self._f18b, fill=(255, 255, 255),
                        tag=span_tags.INVOICE_NUMBER, undersampling=False)

        y = header_height + self.mm(15)

        # --- INFORMAČNÍ KARTY ---
        card_height = self.mm(35)
        card_width = (self._A4_W_PX - margin_l - margin_r - self.mm(15)) // 3

        # Karta 1 - Dodavatel
        card1_x = margin_l
        d.rectangle((card1_x, y, card1_x + card_width, y + card_height), 
                    fill=(255, 255, 255), outline=PRIMARY, width=2)
        d.rectangle((card1_x, y, card1_x + card_width, y + self.mm(6)), fill=PRIMARY)
        
        self._text(d,(card1_x + self.mm(3), y + self.mm(1)), "PRODÁVAJÍCÍ", font=self._f10b, fill=(255, 255, 255))
        self._text(d,(card1_x + self.mm(3), y + self.mm(8)), self._safe(self.supplier.name), font=self._f11b, fill=DARK)
        self._text(d,(card1_x + self.mm(3), y + self.mm(13)), self._safe(self.supplier.address)[:25], font=self._f9, fill=DARK)
        self._text(d,(card1_x + self.mm(3), y + self.mm(17)), label="IČ:", text=f"{self._safe(self.supplier.register_id)}", font=self._f9, fill=DARK,
                    span_tag=span_tags.SUPPLIER_REGISTER_ID, hard_undersampling=False)
        self._text(d,(card1_x + self.mm(3), y + self.mm(24)), label="DIČ:", text=f"{self._safe(self.supplier.tax_id)}", font=self._f9, fill=DARK,
                    span_tag=span_tags.SUPPLIER_TAX_ID, hard_undersampling=False)

        # Karta 2 - Kupující  
        card2_x = margin_l + card_width + self.mm(7.5)
        d.rectangle((card2_x, y, card2_x + card_width, y + card_height), 
                    fill=(255, 255, 255), outline=ACCENT, width=2)
        d.rectangle((card2_x, y, card2_x + card_width, y + self.mm(6)), fill=ACCENT)
        
        self._text(d,(card2_x + self.mm(3), y + self.mm(1)), "KUPUJÍCÍ", font=self._f10b, fill=(255, 255, 255))
        self._text(d,(card2_x + self.mm(3), y + self.mm(8)), self._safe(self.customer.name), font=self._f11b, fill=DARK)
        self._text(d,(card2_x + self.mm(3), y + self.mm(13)), self._safe(self.customer.address)[:25], font=self._f9, fill=DARK)
        self._text(d,(card2_x + self.mm(3), y + self.mm(17)), label="IČ:", text=f"{self._safe(self.customer.register_id)}", font=self._f9, fill=DARK,
                    span_tag=span_tags.CUSTOMER_REGISTER_ID, hard_undersampling=False)
        self._text(d,(card2_x + self.mm(3), y + self.mm(24)), label="DIČ:", text=f"{self._safe(self.customer.tax_id)}", font=self._f9, fill=DARK,
                    span_tag=span_tags.CUSTOMER_TAX_ID, hard_undersampling=False)

        # Karta 3 - Platba
        card3_x = margin_l + 2 * card_width + self.mm(15)
        d.rectangle((card3_x, y, card3_x + card_width, y + card_height), 
                    fill=(255, 255, 255), outline=SECONDARY, width=2)
        d.rectangle((card3_x, y, card3_x + card_width, y + self.mm(6)), fill=SECONDARY)
        
        self._text(d,(card3_x + self.mm(3), y + self.mm(1)), "PLATBA", font=self._f10b, fill=(255, 255, 255))
        self._text(d,(card3_x + self.mm(3), y + self.mm(8)), label="Datum:", text=f"{self._safe(self.issue_date)}", font=self._f9, fill=DARK,
                    span_tag=span_tags.ISSUE_DATE, hard_undersampling=False)
        self._text(d,(card3_x + self.mm(3), y + self.mm(12)), label="Splatnost:", text=f"{self._safe(self.due_date)}", font=self._f9, fill=DARK, span_tag=span_tags.DUE_DATE, hard_undersampling=False)
        self._text(d,(card3_x + self.mm(3), y + self.mm(16)), label="VS: ", text=f"{self._safe(self.variable_symbol)}", font=self._f9, fill=DARK, span_tag=span_tags.VARIABLE_SYMBOL, hard_undersampling=False)

        y += card_height + self.mm(20)

        # --- STYLIZOVANÁ TABULKA ---
        headers = ["Popis služby", "Množství", "Jednotka", "Cena/ks", "DPH%", "Celkem"]
        col_widths = [0.4, 0.12, 0.08, 0.15, 0.08, 0.17]
        table_width = self._A4_W_PX - margin_l - margin_r
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin_l + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička s gradientem
        header_height = self.mm(10)
        for i in range(10):
            step_height = header_height // 10
            ratio = i / 10
            r = int(ACCENT[0] * (1 - ratio) + PRIMARY[0] * ratio)
            g = int(ACCENT[1] * (1 - ratio) + PRIMARY[1] * ratio) 
            b = int(ACCENT[2] * (1 - ratio) + PRIMARY[2] * ratio)
            
            d.rectangle((margin_l, y + i * step_height, self._A4_W_PX - margin_r, 
                       y + (i + 1) * step_height), fill=(r, g, b))

        # Texty hlavičky
        for i, header in enumerate(headers):
            text_x = x_cols[i] + self.mm(3)
            if i in [1, 2, 4]:  # Střed pro množství, jednotku, DPH
                text_x = x_cols[i] + col_abs[i] // 2
                self._draw_center(d, text_x, y + self.mm(2.5), header, self._f10b, (255, 255, 255))
            elif i in [3, 5]:  # Doprava pro ceny
                text_x = x_cols[i] + col_abs[i] - self.mm(3)
                self._draw_right(d, text_x, y + self.mm(2.5), header, self._f10b, (255, 255, 255))
            else:  # Vlevo pro popis
                self._text(d,(text_x, y + self.mm(2.5)), header, font=self._f10b, fill=(255, 255, 255))

        y += header_height

        # Řádky s alternujícím pozadím
        row_height = self.mm(8)
        for i, item in enumerate(self.items):
            bg_color = (255, 255, 255) if i % 2 == 0 else (245, 247, 250)
            d.rectangle((margin_l, y, self._A4_W_PX - margin_r, y + row_height), fill=bg_color)
            
            row_data = [
                self._safe(item.description),
                str(self._safe(item.quantity)),
                "ks",
                self._fmt_money(item.ppu),
                f"{self._safe(item.vat_percentage)}%",
                self._fmt_money(item.price_with_vat)
            ]
            
            for j, data in enumerate(row_data):
                text_y = y + self.mm(2)
                if j in [1, 2, 4]:  # Střed
                    self._draw_center(d, x_cols[j] + col_abs[j] // 2, text_y, data, self._f9, DARK)
                elif j in [3, 5]:  # Doprava
                    self._draw_right(d, x_cols[j] + col_abs[j] - self.mm(3), text_y, data, self._f9, DARK)
                else:  # Vlevo
                    self._text(d,(x_cols[j] + self.mm(3), text_y), data, font=self._f9, fill=DARK)
            
            y += row_height

        # --- CELKOVÁ ČÁSTKA S EFEKTEM ---
        y += self.mm(15)
        
        # Stínovaný box pro celkovou sumu
        shadow_offset = 3
        total_box_w = self.mm(70)
        total_box_h = self.mm(18)
        total_x = self._A4_W_PX - margin_r - total_box_w
        
        # Stín
        d.rectangle((total_x + shadow_offset, y + shadow_offset, 
                    total_x + total_box_w + shadow_offset, y + total_box_h + shadow_offset), 
                    fill=(200, 200, 200))
        
        # Hlavní box
        d.rectangle((total_x, y, total_x + total_box_w, y + total_box_h), fill=PRIMARY)
        
        # Text
        total_text = f"CELKEM K ÚHRADĚ"
        self._draw_center(d, total_x + total_box_w // 2, y + self.mm(4), 
                            total_text, self._f11b, (255, 255, 255), undersampling=False)
        
        self._draw_center(d, total_x + total_box_w // 2, y + self.mm(10), 
                            text=f"{self._fmt_money(self.calculated_total_price)}",
                            end=f"{self.currency.value}", font=self._f16b, fill=(255, 255, 255), tag=span_tags.TOTAL, undersampling=False)

        # Uložení
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=self._TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+self.mm(3)),word.tag.value, font=self._f10, fill=self._TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")

        return True