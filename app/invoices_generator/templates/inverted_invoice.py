from datetime import datetime
import json
from typing import Any, Dict, Optional, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

import pytesseract
from app.invoices_generator.core.enumerates.relationship_types import relationship_types
from app.invoices_generator.core.enumerates.span_tags import span_tags
from app.invoices_generator.core.invoice import invoice
from app.invoices_generator.core.relationship import relationship
from app.invoices_generator.utility.json_encoder import json_encoder

@final
class inverted_invoice(invoice):

    def to_json_donut(self) -> Any:
        data = dict(supplier_name = self.supplier.name, customer_name = self.customer.name,
                    issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date = self.taxable_supply_date,
                    payment=self.payment.value, BIC="", bank_account_number="", IBAN="",
                    variable_symbol=self.variable_symbol, const_symbol="",
                    supplier_register_id=self.supplier.register_id, supplier_tax_id=self.supplier.tax_id,
                    customer_register_id=self.customer.register_id, customer_tax_id=self.customer.tax_id,
                    vat_items=self.vat,
                    total_price=self.calculated_total_price, total_vat=None, currency=self.currency,
                    invoice_number=self.invoice_number)

        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False, sort_keys=True))

        return j_data

    def generate_img(self, output_path: str) -> bool:
        margin = self.mm(25)
        
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        # --- HLAVIČKA A INFO O FAKTUŘE ---
        y = margin
        self._text(d,(margin, y), label=f"Faktura / Daňový doklad č.", text=f"{self._safe(self.invoice_number)}", font=self._f17b, fill=self._INK, span_tag=span_tags.INVOICE_NUMBER, hard_undersampling=False)
        
        y += self.mm(10)
        self._text(d,(margin, y), label="Datum vystavení:", text=f"{self._safe(self.issue_date)}", font=self._f11, fill=self._INK, span_tag=span_tags.ISSUE_DATE, hard_undersampling=False)
        self._text(d,(margin, y + self.mm(5)), label=f"Datum splatnosti:", text=f"{self._safe(self.due_date)}", font=self._f11, fill=self._INK, span_tag=span_tags.DUE_DATE, hard_undersampling=False)
        self._text(d,(margin, y + self.mm(10)), label=f"Způsob úhrady: ", text=f"{self._safe(self.payment.value)}", font=self._f11, fill=self._INK, span_tag=span_tags.PAYMENT_TYPE, hard_undersampling=False)
        self._text(d,(margin, y + self.mm(15)), label=f"Variabilní symbol:", text=f"{self._safe(self.variable_symbol)}", font=self._f11b, fill=self._INK, span_tag=span_tags.VARIABLE_SYMBOL, hard_undersampling=False)

        # Adresy v bloku vpravo
        address_block_x = self._A4_W_PX - margin - self.mm(80)
        y_address = margin + self.mm(10)
        self._text(d,(address_block_x, y_address), "DODAVATEL:", font=self._f12b, fill=self._INK)
        y_address += self.mm(6)
        self._text(d,(address_block_x, y_address), self._safe(self.supplier.name), font=self._f11b, fill=self._INK)
        y_address += self.mm(5)
        self._text(d,(address_block_x, y_address), self._safe(self.supplier.address), font=self._f11, fill=self._INK)
        y_address += self.mm(5)
        x_end, _ = self._text(d,(address_block_x, y_address), label="IČ:",text=f"{self._safe(self.supplier.register_id)}", font=self._f11, fill=self._INK, span_tag=span_tags.SUPPLIER_REGISTER_ID, hard_undersampling=False)
        self._text(d,(x_end, y_address), label="| DIČ:",text=f"{self._safe(self.supplier.tax_id)}", font=self._f11, fill=self._INK, span_tag=span_tags.SUPPLIER_TAX_ID, hard_undersampling=False)
        
        y_address += self.mm(10)
        self._text(d,(address_block_x, y_address), "ODBĚRATEL:", font=self._f12b, fill=self._INK)
        y_address += self.mm(6)
        self._text(d,(address_block_x, y_address), self._safe(self.customer.name), font=self._f11b, fill=self._INK)
        y_address += self.mm(5)
        self._text(d,(address_block_x, y_address), self._safe(self.customer.address), font=self._f11, fill=self._INK)
        y_address += self.mm(5)
        x_end, _ = self._text(d,(address_block_x, y_address), label="IČ: ", text=f"{self._safe(self.customer.register_id)}", font=self._f11, fill=self._INK,
                            span_tag=span_tags.CUSTOMER_REGISTER_ID, hard_undersampling=False)
        self._text(d,(x_end, y_address), label="DIČ: ", text=f"{self._safe(self.customer.tax_id)}", font=self._f11, fill=self._INK,
                            span_tag=span_tags.CUSTOMER_TAX_ID, hard_undersampling=False)

        y = max(y + self.mm(25), y_address + self.mm(10))

        # --- SOUHRN DPH NAD TABULKOU ---
        y += self.mm(10)
        
        # Levé zarovnání souhrnu
        summary_x = margin
        self._text(d,(summary_x, y), "Přehled DPH:", font=self._f12b, fill=self._INK, hard_undersampling=False)
        y += self.mm(5)
        
        for v in self.vat:
            x_end, vat_id = self._text(d,(summary_x, y), label="Sazba", text=f"{self._safe(v.vat_percentage)}", end="%",font=self._f10, fill=self._INK, span_tag=span_tags.VAT_PERCENTAGE, hard_undersampling=False)
            x_end, base_id = self._text(d,(x_end, y), label="Základ", text=f"{self._safe(v.vat_base)}", font=self._f10, fill=self._INK, span_tag=span_tags.VAT_BASE, hard_undersampling=False)
            x_end, percentage_id = self._text(d,(x_end, y), label="DPH", text=f"{self._safe(v.vat)}",font=self._f10, fill=self._INK, span_tag=span_tags.VAT, hard_undersampling=False)
            
            self._relationships.append(relationship(base_id, percentage_id, relationship_types.BASE_OF))
            self._relationships.append(relationship(vat_id, percentage_id, relationship_types.VAT_OF))

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
                self._text(d,(x_cols[i] + 6, baseline), h, font=self._f11b, fill=self._INK)
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
            self._text(d,(x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=self._INK)
            self._draw_right(d, x_cols[1] + col_abs[1] - 6, y_text, cells[1], self._f11, fill=self._INK)
            self._draw_right(d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], self._f11, fill=self._INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], self._f11, fill=self._INK)

        y += self.mm(5)
        
        # --- CELKOVÁ SUMA V PRAVÉM DOLNÍM ROHU ---
        total_box_x = self._A4_W_PX - margin - self.mm(70)
        total_box_w = self.mm(70)
        y_total = y + self.mm(10)
        
        self._text(d,(total_box_x, y_total), "Celkem k úhradě:", font=self._f13b, fill=self._INK, hard_undersampling=False)
        self._draw_right(d, total_box_x + total_box_w, y_total,text=f"{self._fmt_money(self.calculated_total_price)}", end=f"{self.currency.value}", font=self._f13b, fill=self._INK, tag=span_tags.TOTAL, undersampling=False)

        # --- PATIČKA ---
        footer_y = self._A4_H_PX - self.mm(30)
        d.line([(margin, footer_y), (self._A4_W_PX - margin, footer_y)], fill=self._LINE_STRONG, width=2)
        footer_y += self.mm(5)
        
        self._text(d,(margin, footer_y), "Platbu prosím proveďte na výše uvedený bankovní účet.", font=self._f11, fill=self._INK)
        self._draw_right(d, self._A4_W_PX - margin, footer_y, f"Datum tisku: {datetime.now().strftime('%d.%m.%Y')}", font=self._f11, fill=self._INK)
        
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=self._TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+self.mm(3)),word.tag.value, font=self._f10, fill=self._TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")

        return True