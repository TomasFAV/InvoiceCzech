from datetime import datetime
from typing import final

from PIL import Image, ImageDraw

from invoice_annotator.utils.GRelationship import GRelationship
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice

from invoices_generator.utility.invoice_consts import INK, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money


@final
class simple_invoice(DInvoice):

    def generate_img(self, output_path: str) -> bool:
        margin_l = mm(20)
        margin_r = mm(20)
        margin_t = mm(20)
        
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        y = margin_t

        # --- ZÁVĚREČNÁ SUMA Nahoře ---
        total_price_x = self._A4_W_PX - margin_r - mm(40)
        self._text(d,(total_price_x, y), "CELKEM K ZAPLACENÍ", font=self._f13b, fill=INK)
        y += mm(5)
        self._text(d,(total_price_x, y), text=f"{fmt_money(self.calculated_total_price)}", end=f"{self.currency.value}", font=self._f17b, fill=INK, span_tag=span_tags.TOTAL)
        
        # Datové pole uprostřed nahoře
        date_box_x = self._A4_W_PX / 2
        
        self._draw_center(d, date_box_x, margin_t, "FAKTURA", self._f17b, INK)
        self._draw_center(d, date_box_x, margin_t + mm(8), label=f"Číslo faktury: ", text=f"{safe(self.invoice_number)}", font=self._f13b, fill=INK,
                            span_tag=span_tags.INVOICE_NUMBER)
        
        y += mm(15)
        hr(y, "strong")
        y += mm(5)
        
        # --- BLOKY INFORMACÍ PROHOZENÉ ---
        # Bankovní účet a symboly - Nalevo
        bank_x = margin_l
        self._text(d,(bank_x, y), "Platební údaje:", font=self._f12b, fill=INK)
        y += mm(5)
        self._text(d,(bank_x, y), label="Bankovní účet:", text=f"{safe(self.bank_account_number)}", font=self._f11, fill=INK, span_tag=span_tags.BANK_ACCOUNT_NUMBER)
        y += mm(5)
        self._text(d,(bank_x, y), label="IBAN: ", text=f"{safe(self.IBAN)}", font=self._f11, fill=INK, span_tag=span_tags.IBAN)
        y += mm(5)
        self._text(d,(bank_x, y), label="Variabilní symbol: ", text=f"{safe(self.variable_symbol)}", font=self._f11b, fill=INK, span_tag=span_tags.VARIABLE_SYMBOL)

        # Datové pole - Napravo
        dates_x = self._A4_W_PX - margin_r - mm(50)
        self._text(d,(dates_x, y - mm(15)), "Datum vystavení:", font=self._f11, fill=INK)
        self._text(d,(dates_x + mm(30), y - mm(15)), safe(self.issue_date), font=self._f11b, fill=INK, span_tag=span_tags.ISSUE_DATE)
        
        self._text(d,(dates_x, y - mm(10)), "Datum splatnosti:", font=self._f11, fill=INK)
        self._text(d,(dates_x + mm(30), y - mm(10)), safe(self.due_date), font=self._f11b, fill=INK, span_tag=span_tags.DUE_DATE)
        
        self._text(d,(dates_x, y - mm(5)), "Způsob platby:", font=self._f11, fill=INK)
        self._text(d,(dates_x + mm(30), y - mm(5)), safe(self.payment_type), font=self._f11b, fill=INK, span_tag=span_tags.PAYMENT_TYPE)

        # --- DODAVATEL / ODBĚRATEL VE STŘEDU ---
        y_middle = y + mm(5)
        
        # Dodavatel
        self._draw_center(d, self._A4_W_PX / 2, y_middle, "DODAVATEL", self._f12b, INK)
        self._draw_center(d, self._A4_W_PX / 2, y_middle + mm(5), safe(self.supplier.name), self._f11b, INK)
        self._draw_center(d, self._A4_W_PX / 2, y_middle + mm(10), safe(self.supplier.address), self._f11, INK)
        x_end, _ = self._draw_center(d, self._A4_W_PX / 2, y_middle + mm(15), label=f"IČ: ", text=f"{safe(self.supplier.register_id)}", font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_REGISTER_ID)
        self._text(d, (x_end, y_middle + mm(15)), label=f"DIČ: ", text=f"{safe(self.supplier.tax_id)}", font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_TAX_ID)
        y = y_middle + mm(25)
        
        # Odběratel
        self._draw_center(d, self._A4_W_PX / 2, y, "ODBĚRATEL", self._f12b, INK)
        self._draw_center(d, self._A4_W_PX / 2, y + mm(5), safe(self.customer.name), self._f11b, INK)
        self._draw_center(d, self._A4_W_PX / 2, y + mm(10), safe(self.customer.address), self._f11, INK)       
        x_end, _ = self._draw_center(d, self._A4_W_PX / 2, y + mm(15), label=f"IČ: ", text=f"{safe(self.customer.register_id)}", font=self._f11, fill=INK, span_tag=span_tags.CUSTOMER_REGISTER_ID)
        self._text(d, (x_end, y + mm(15)), label=f"DIČ: ", text=f"{safe(self.customer.tax_id)}", font=self._f11, fill=INK, span_tag=span_tags.CUSTOMER_TAX_ID)

        y += mm(25)
        hr(y, "strong")
        y += mm(5)
        
        # --- TABULKA POLOŽEK ---
        table_w = self._A4_W_PX - 2 * margin_l
        headers = ["Popis zboží", "Cena ks bez DPH", "DPH %", "Celkem s DPH"]
        col_ws = [0.45, 0.20, 0.15, 0.20]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin_l]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        head_h = mm(7)
        baseline = y + mm(2)
        
        for i, h in enumerate(headers):
            if i == 0:
                self._text(d,(x_cols[i] + 6, baseline), h, font=self._f11b, fill=INK, must_have_same_width=True)
            else:
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, baseline, h, self._f11b, INK, must_have_same_width=True)
        
        y += head_h
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)
        
        row_h = mm(6.5)
        for it in self.items:
            y += row_h
            d.line((margin_l, y, margin_l + table_w, y), fill=LINE, width=1)
            
            cells = [
                f"{safe(it.quantity)}x {safe(it.description)}",
                fmt_money(it.ppu),
                f"{safe(it.vat_percentage)}%",
                fmt_money(it.price_with_vat),
            ]
            
            y_text = y - row_h + mm(2)
            self._text(d,(x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=INK)
            self._draw_right(d, x_cols[1] + col_abs[1] - 6, y_text, cells[1], self._f11, INK)
            self._draw_right(d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], self._f11, INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], self._f11, INK)

        y += mm(2)
        hr(y, "strong")
        y += mm(5)

        # --- PATIČKA ---
        
        # QR Kód a poznámky - dole
        qr_size = mm(20)
        qr_x = mm(20)
        qr_y = self._A4_H_PX - mm(40)
        d.rectangle((qr_x, qr_y, qr_x + qr_size, qr_y + qr_size), outline=LINE, width=2, fill=None)
        self._draw_center(d, qr_x + qr_size / 2, qr_y + qr_size / 2, "QR", self._f10, (170, 170, 170))
        
        self._text(d,(qr_x + qr_size + mm(5), qr_y), "Děkujeme za Váš nákup.", font=self._f11, fill=INK)
        self._text(d,(qr_x + qr_size + mm(5), qr_y + mm(5)), "Faktura byla vygenerována automaticky.", font=self._f10, fill=INK)
        
        # Souhrny DPH - vpravo dole
        vat_summary_x = self._A4_W_PX - margin_r - mm(80)
        y_vat = self._A4_H_PX - mm(35)
        self._text(d,(vat_summary_x, y_vat), "Souhrn DPH:", font=self._f11b, fill=INK)
        y_vat += mm(5)
        for v in self.vat:
            x_end, percentage_id = self._text(d,(vat_summary_x, y_vat), label="Sazba", text=f"{safe(v.vat_percentage)}", end="%",font=self._f10, fill=INK, span_tag=span_tags.VAT_PERCENTAGE)
            x_end, base_id = self._text(d,(x_end, y_vat), label="Základ", text=f"{safe(v.vat_base)}", font=self._f10, fill=INK, span_tag=span_tags.VAT_BASE)
            x_end, vat_id = self._text(d,(x_end, y_vat), label="DPH", text=f"{safe(v.vat)}",font=self._f10, fill=INK, span_tag=span_tags.VAT)
            y_vat += mm(4)

            self.append_relationship(GRelationship(None, base_id, percentage_id, relationship_types.BASE_OF))
            self.append_relationship(GRelationship(None, vat_id, percentage_id, relationship_types.VAT_OF))

        hr(self._A4_H_PX - mm(15), "strong")
        
        self._draw_center(d, self._A4_W_PX / 2, self._A4_H_PX - mm(12), "Strana 1 z 1", self._f10, INK)
        self._text(d,(self._A4_W_PX - margin_r, self._A4_H_PX - mm(12)), f"Tisk: {datetime.now().strftime('%d.%m.%Y %H:%M')}", font=self._f10, fill=INK)

        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+mm(3)),word.tag.value, font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")
        return True
