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
class compact_invoice(DInvoice):
    """Kompaktní faktura s hustším layoutem a menšími fonty"""
    
    
    def generate_img(self, output_path: str) -> bool:
        # Menší okraje pro kompaktní design
        margin = mm(10)
        
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), (255, 255, 255))
        d = ImageDraw.Draw(img)

        DARK_BLUE = (25, 42, 86)
        LIGHT_BLUE = (74, 144, 226)
        GRAY = (95, 99, 104)

        y = margin

        # --- KOMPAKTNÍ HLAVIČKA ---
        # Barevný pruh nahoře
        d.rectangle((0, 0, self._A4_W_PX, mm(6)), fill=DARK_BLUE)
        
        y += mm(8)
        
        # Informace v jednom řádku
        self._text(d,(margin, y), label=f"{safe(self.supplier.name)} | FAKTURA", text=f"{safe(self.invoice_number)}", 
                    font=self._f14b, fill=DARK_BLUE, span_tag=span_tags.INVOICE_NUMBER)
        
        # Datum vpravo
        self._draw_right(d, self._A4_W_PX - margin, y, label="Datum: ", text=f"{safe(self.issue_date)}", 
                        font=self._f12, fill=GRAY, span_tag=span_tags.ISSUE_DATE)
        
        y += mm(12)

        # --- ÚDAJE VE DVOU SLOUPCÍCH ---
        col_width = (self._A4_W_PX - 2 * margin - mm(10)) // 2
        
        # Levý sloupec - dodavatel
        self._text(d,(margin, y), "DODAVATEL", font=self._f10b, fill=LIGHT_BLUE)
        y += mm(4)
        self._text(d,(margin, y), safe(self.supplier.name), font=self._f11b, fill=DARK_BLUE)
        y += mm(4)
        self._text(d,(margin, y), safe(self.supplier.address), font=self._f9, fill=GRAY)
        y += mm(3)
        x_end, _ = self._text(d,(margin, y), label="IČ: ", text=f"{safe(self.supplier.register_id)}", 
                            font=self._f9, fill=GRAY, span_tag=span_tags.SUPPLIER_REGISTER_ID)
        self._text(d,(x_end, y), label="| DIČ: ", text=f"{safe(self.supplier.tax_id)}", 
                            font=self._f9, fill=GRAY, span_tag=span_tags.SUPPLIER_TAX_ID)

        # Pravý sloupec - odběratel
        customer_x = margin + col_width + mm(10)
        customer_y = y - mm(11)  # Začínáme na stejné výši
        
        self._text(d,(customer_x, customer_y), "ODBĚRATEL", font=self._f10b, fill=LIGHT_BLUE)
        customer_y += mm(4)
        self._text(d,(customer_x, customer_y), safe(self.customer.name), font=self._f11b, fill=DARK_BLUE)
        customer_y += mm(4)
        self._text(d,(customer_x, customer_y), safe(self.customer.address), font=self._f9, fill=GRAY)
        customer_y += mm(3)
        self._text(d,(customer_x, customer_y), label="IČ: ", text=f"{safe(self.customer.register_id)}", font=self._f9, fill=GRAY, span_tag=span_tags.CUSTOMER_REGISTER_ID)
        customer_y += mm(3)
        self._text(d,(customer_x, customer_y), label="DIČ: ", text=f"{safe(self.customer.tax_id)}", font=self._f9, fill=GRAY, span_tag=span_tags.CUSTOMER_TAX_ID)
        
        y += mm(15)

        # --- PLATEBNÍ INFO V ŘÁDKU ---
        x_end, _ = self._text(d,(margin, y), label="Splatnost: ", text=f"{safe(self.due_date)}",font=self._f10, fill=GRAY, span_tag=span_tags.DUE_DATE)
        x_end, _ = self._text(d,(x_end, y), label="| Platba: ", text=f"{safe(self.payment_type)}",font=self._f10, fill=GRAY, span_tag=span_tags.PAYMENT_TYPE)
        x_end, _ = self._text(d,(x_end, y), label="| VS: ", text=f"{safe(self.variable_symbol)}",font=self._f10, fill=GRAY, span_tag=span_tags.VARIABLE_SYMBOL)

        y += mm(10)
        
        # Tenká linka
        d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=LIGHT_BLUE, width=1)
        y += mm(8)

        # --- KOMPAKTNÍ TABULKA ---
        headers = ["Položka", "Ks", "Cena", "Celkem"]
        col_widths = [0.6, 0.1, 0.15, 0.15]
        table_width = self._A4_W_PX - 2 * margin
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička tabulky
        header_height = mm(8)
        for i, header in enumerate(headers):
            if i == 0:  # Položka vlevo
                self._text(d,(x_cols[i] + mm(2), y), header, font=self._f10b, fill=DARK_BLUE, must_have_same_width=True)
            elif i == 1:  # Ks na střed
                self._draw_center(d, x_cols[i] + col_abs[i] // 2, y, header, self._f10b, DARK_BLUE, must_have_same_width=True)
            else:  # Ceny doprava
                self._draw_right(d, x_cols[i] + col_abs[i] - mm(2), y, header, self._f10b, DARK_BLUE, must_have_same_width=True)

        y += header_height
        d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=DARK_BLUE, width=2)

        # Řádky položek
        row_height = mm(6)
        for item in self.items:
            y += row_height
            
            # Obsah řádku
            self._text(d,(x_cols[0] + mm(2), y - mm(4)), safe(item.description)[:40], font=self._f9, fill=DARK_BLUE)
            
            self._draw_center(d, x_cols[1] + col_abs[1] // 2, y - mm(4), 
                            str(safe(item.quantity)), self._f9, DARK_BLUE)
            
            self._draw_right(d, x_cols[2] + col_abs[2] - mm(2), y - mm(4), 
                            fmt_money(item.ppu), self._f9, DARK_BLUE)
            
            self._draw_right(d, x_cols[3] + col_abs[3] - mm(2), y - mm(4), 
                            fmt_money(item.price_with_vat), self._f9, DARK_BLUE)
            
            # Tenká linka
            d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=(220, 220, 220), width=1)

        # Celkova suma
        y += mm(5)
        
        self._draw_right(d, self._A4_W_PX - margin - mm(20), y + mm(2.5), 
                        label="CELKEM: ", text=f"{self.calculated_total_price}",end=f"{self.currency.value}", font=self._f11b, fill=(255, 255, 255),
                        span_tag=span_tags.TOTAL)

        y += mm(20)

        # --- PLATEBNÍ ÚDAJE V PATIČCE ---
        self._text(d,(margin, y), label="Číslo účtu: ", text=f"{safe(self.bank_account_number)}", font=self._f9, fill=GRAY,
                    span_tag=span_tags.BANK_ACCOUNT_NUMBER)

        # Uložení
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+mm(3)),word.tag.value, font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")
        return True
