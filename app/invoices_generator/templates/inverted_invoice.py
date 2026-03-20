from datetime import datetime
from typing import final

from PIL import Image, ImageDraw
from decimal import ROUND_HALF_UP

from invoice_annotator.utils.GRelationship import GRelationship
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money

@final
class inverted_invoice(DInvoice):


    def generate_img(self, output_path: str) -> bool:
        margin = mm(25)
        
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        # --- HLAVIČKA A INFO O FAKTUŘE ---
        y = margin
        self._text(d,(margin, y), label=f"Faktura / Daňový doklad č.", text=f"{safe(self.invoice_number)}", font=self._f17b, fill=INK, span_tag=span_tags.INVOICE_NUMBER)
        
        y += mm(10)
        self._text(d,(margin, y), label="Datum vystavení:", text=f"{safe(self.issue_date)}", font=self._f11, fill=INK, span_tag=span_tags.ISSUE_DATE)
        self._text(d,(margin, y + mm(5)), label=f"Datum splatnosti:", text=f"{safe(self.due_date)}", font=self._f11, fill=INK, span_tag=span_tags.DUE_DATE)
        self._text(d,(margin, y + mm(10)), label=f"Způsob úhrady: ", text=f"{safe(self.payment_type)}", font=self._f11, fill=INK, span_tag=span_tags.PAYMENT_TYPE)
        self._text(d,(margin, y + mm(15)), label=f"Variabilní symbol:", text=f"{safe(self.variable_symbol)}", font=self._f11b, fill=INK, span_tag=span_tags.VARIABLE_SYMBOL)

        # Adresy v bloku vpravo
        address_block_x = self._A4_W_PX - margin - mm(80)
        y_address = margin + mm(10)
        self._text(d,(address_block_x, y_address), "DODAVATEL:", font=self._f12b, fill=INK)
        y_address += mm(6)
        self._text(d,(address_block_x, y_address), safe(self.supplier.name), font=self._f11b, fill=INK)
        y_address += mm(5)
        self._text(d,(address_block_x, y_address), safe(self.supplier.address), font=self._f11, fill=INK)
        y_address += mm(5)
        x_end, _ = self._text(d,(address_block_x, y_address), label="IČ:",text=f"{safe(self.supplier.register_id)}", font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_REGISTER_ID)
        self._text(d,(x_end, y_address), label="| DIČ:",text=f"{safe(self.supplier.tax_id)}", font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_TAX_ID)
        
        y_address += mm(10)
        self._text(d,(address_block_x, y_address), "ODBĚRATEL:", font=self._f12b, fill=INK)
        y_address += mm(6)
        self._text(d,(address_block_x, y_address), safe(self.customer.name), font=self._f11b, fill=INK)
        y_address += mm(5)
        self._text(d,(address_block_x, y_address), safe(self.customer.address), font=self._f11, fill=INK)
        y_address += mm(5)
        x_end, _ = self._text(d,(address_block_x, y_address), label="IČ: ", text=f"{safe(self.customer.register_id)}", font=self._f11, fill=INK,
                            span_tag=span_tags.CUSTOMER_REGISTER_ID)
        self._text(d,(x_end, y_address), label="DIČ: ", text=f"{safe(self.customer.tax_id)}", font=self._f11, fill=INK,
                            span_tag=span_tags.CUSTOMER_TAX_ID)

        y = max(y + mm(25), y_address + mm(10))

        # --- SOUHRN DPH NAD TABULKOU ---
        y += mm(10)
        
        # Levé zarovnání souhrnu
        summary_x = margin
        self._text(d,(summary_x, y), "Přehled DPH:", font=self._f12b, fill=INK)
        y += mm(5)
        
        for v in self.vat:
            x_end, vat_id = self._text(d,(summary_x, y), label="Sazba", text=f"{safe(v.vat_percentage)}", end="%",font=self._f10, fill=INK, span_tag=span_tags.VAT_PERCENTAGE)
            x_end, base_id = self._text(d,(x_end, y), label="Základ", text=f"{fmt_money(safe(v.vat_base))}", font=self._f10, fill=INK, span_tag=span_tags.VAT_BASE)
            x_end, percentage_id = self._text(d,(x_end, y), label="DPH", text=f"{fmt_money(safe(v.vat))}",font=self._f10, fill=INK, span_tag=span_tags.VAT)
            
            self.append_relationship(GRelationship(None, base_id, percentage_id, relationship_types.BASE_OF))
            self.append_relationship(GRelationship(None, vat_id, percentage_id, relationship_types.VAT_OF))

            y += mm(5)

        y += mm(5)
        d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=LINE_STRONG, width=2)
        y += mm(5)

        # --- TABULKA POLOŽEK ---
        table_w = self._A4_W_PX - 2 * margin
        
        headers = ["Popis zboží/služby", "Ks", "Jednotková cena", "Celkem"]
        col_ws = [0.4, 0.1, 0.25, 0.25]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        head_h = mm(7)
        baseline = y + mm(2)
        for i, h in enumerate(headers):
            if i == 0:
                self._text(d,(x_cols[i] + 6, baseline), h, font=self._f11b, fill=INK, must_have_same_width=True)
            else:
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, baseline, h, self._f11b, fill=INK, must_have_same_width=True)
        
        y += head_h
        d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=LINE_STRONG, width=2)
        
        row_h = mm(6.5)
        for it in self.items:
            y += row_h
            d.line([(margin, y), (self._A4_W_PX - margin, y)], fill=LINE, width=1)
            
            cells = [
                safe(it.description),
                safe(it.quantity),
                fmt_money(it.ppu),
                fmt_money(it.price_with_vat),
            ]
            
            y_text = y - row_h + mm(2)
            self._text(d,(x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=INK)
            self._draw_right(d, x_cols[1] + col_abs[1] - 6, y_text, cells[1], self._f11, fill=INK)
            self._draw_right(d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], self._f11, fill=INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], self._f11, fill=INK)

        y += mm(5)
        
        # --- CELKOVÁ SUMA V PRAVÉM DOLNÍM ROHU ---
        total_box_x = self._A4_W_PX - margin - mm(70)
        total_box_w = mm(70)
        y_total = y + mm(10)
        
        self._text(d,(total_box_x, y_total), "Celkem k úhradě:", font=self._f13b, fill=INK)
        self._draw_right(d, total_box_x + total_box_w, y_total,text=f"{fmt_money(self.calculated_total_price)}", end=f"{self.currency.value}", font=self._f13b, fill=INK, span_tag=span_tags.TOTAL)

        # --- PATIČKA ---
        footer_y = self._A4_H_PX - mm(30)
        d.line([(margin, footer_y), (self._A4_W_PX - margin, footer_y)], fill=LINE_STRONG, width=2)
        footer_y += mm(5)
        
        self._text(d,(margin, footer_y), "Platbu prosím proveďte na výše uvedený bankovní účet.", font=self._f11, fill=INK)
        self._draw_right(d, self._A4_W_PX - margin, footer_y, f"Datum tisku: {datetime.now().strftime('%d.%m.%Y')}", font=self._f11, fill=INK)
        
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+mm(3)),word.tag.value, font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")
        return True
