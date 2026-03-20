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
class martinus_invoice(DInvoice):

    def generate_img(self, output_path: str) -> bool:
        # Margins
        margin_l = mm(20)
        margin_r = mm(20)
        margin_t = mm(15)
        margin_b = mm(15)

        # Canvas
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        # Helper function for horizontal lines
        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        y = margin_t

        # --- TOP SECTION WITH BARCODE AND SHIPPING INFO ---
        # Left side - Barcode and ZAS label
        barcode_x = margin_l
        self._text(d, (barcode_x, y), text="ZAS", font=self._f16b, fill=INK)
        y_barcode = y + mm(8)
        
        # Draw barcode placeholder
        barcode_w = mm(25)
        barcode_h = mm(15)
        d.rectangle((barcode_x, y_barcode, barcode_x + barcode_w, y_barcode + barcode_h), 
                   outline=LINE, width=2, fill=BG)
        
        # Order number below barcode
        y_order = y_barcode + barcode_h + mm(3)
        self._text(d, (barcode_x, y_order), text=safe(self.variable_symbol), 
                  font=self._f13b, fill=INK, span_tag=span_tags.VARIABLE_SYMBOL)
        
        # Another barcode below
        y_barcode2 = y_order + mm(8)
        d.rectangle((barcode_x, y_barcode2, barcode_x + barcode_w, y_barcode2 + barcode_h), 
                   outline=LINE, width=2, fill=BG)

        # Right side - Package number and logo
        package_x = self._A4_W_PX - margin_r - mm(80)
        d.rectangle((package_x - mm(5), y, package_x + mm(50), y + mm(15)), 
                   outline=LINE, width=2, fill=BG)
        self._draw_center(d, package_x + mm(22), y + mm(6), 
                         text=safe(self.variable_symbol), font=self._f17b, fill=INK,
                         span_tag=span_tags.VARIABLE_SYMBOL)
        
        # Invoice type label
        y_type = y + mm(17)
        self._draw_right(d, self._A4_W_PX - margin_r, y_type, 
                        text="FAKTURA", font=self._f10, fill=INK)
        self._draw_right(d, self._A4_W_PX - margin_r, y_type + mm(4), 
                        text=safe(self.invoice_number), font=self._f10b, fill=INK,
                        span_tag=span_tags.INVOICE_NUMBER)
        self._draw_right(d, self._A4_W_PX - margin_r, y_type + mm(8), 
                        text="Daňový doklad", font=self._f9, fill=MUTED)

        # Shipping address in left section
        y_ship = y_barcode + mm(2)
        ship_x = barcode_x + barcode_w + mm(10)
        self._text(d, (ship_x, y_ship), text="Tel na zákazníka:", 
                  font=self._f9, fill=MUTED)
        self._text(d, (ship_x + mm(25), y_ship), text=safe(self.customer.phone) if hasattr(self.customer, 'phone') else "", 
                  font=self._f9b, fill=INK)
        
        y_ship += mm(6)
        self._text(d, (ship_x, y_ship), text=safe(self.customer.name), 
                  font=self._f11b, fill=INK)
        y_ship += mm(5)
        self._text(d, (ship_x, y_ship), text=safe(self.customer.address), 
                  font=self._f11, fill=INK)

        # Logo martinus.cz
        logo_y = y + mm(35)
        self._draw_right(d, self._A4_W_PX - margin_r, logo_y, 
                        text="martinus.cz", font=self._f20b, fill=INK)

        y = logo_y + mm(15)
        
        # --- MAIN INFO SECTION ---
        hr(y, "strong")
        y += mm(8)

        # Two column layout
        col_gap = mm(15)
        table_w = self._A4_W_PX - margin_l - margin_r
        col_w = (table_w - col_gap) // 2
        left_x = margin_l
        right_x = margin_l + col_w + col_gap

        # Left column - Supplier (Prodávající)
        self._text(d, (left_x, y), text="Prodávající:", font=self._f11b, fill=INK)
        y_left = y + mm(5)
        
        self._text(d, (left_x, y_left), text=safe(self.supplier.name), font=self._f10, fill=INK)
        y_left += mm(4)
        self._text(d, (left_x, y_left), text=safe(self.supplier.address), font=self._f10, fill=INK)
        y_left += mm(8)
        
        self._text(d, (left_x, y_left), text=f"Tel.: {safe(self.supplier.phone) if hasattr(self.supplier, 'phone') else ''}", 
                  font=self._f9, fill=INK)
        y_left += mm(4)
        self._text(d, (left_x, y_left), text=f"E-mail: {safe(self.supplier.email) if hasattr(self.supplier, 'email') else ''}", 
                  font=self._f9, fill=INK)
        self._text(d, (left_x + mm(20), y_left), text=f"Web: {safe(self.supplier.website) if hasattr(self.supplier, 'website') else ''}", 
                  font=self._f9, fill=INK)
        y_left += mm(8)
        
        self._text(d, (left_x, y_left), text="IČO:", font=self._f9, fill=INK)
        self._text(d, (left_x + mm(10), y_left), text=safe(self.supplier.register_id), 
                  font=self._f9b, fill=INK, span_tag=span_tags.SUPPLIER_REGISTER_ID)
        self._text(d, (left_x + mm(30), y_left), text="DIČ:", font=self._f9, fill=INK)
        self._text(d, (left_x + mm(40), y_left), text=safe(self.supplier.tax_id), 
                  font=self._f9b, fill=INK, span_tag=span_tags.SUPPLIER_TAX_ID)
        self._text(d, (left_x + mm(60), y_left), text="IČ DPH:", font=self._f9, fill=INK)
        self._text(d, (left_x + mm(75), y_left), text=safe(self.supplier.vat_id) if hasattr(self.supplier, 'vat_id') else "", 
                  font=self._f9b, fill=INK)
        y_left += mm(8)
        
        self._text(d, (left_x, y_left), text="Bank account details:", font=self._f9, fill=INK)
        y_left += mm(4)
        self._text(d, (left_x, y_left),
                    label="Číslo účtu:", 
                    text=f"{safe(self.bank_account_number)}", 
                    font=self._f9b, fill=INK, span_tag=span_tags.BANK_ACCOUNT_NUMBER)
        y_left += mm(4)
        self._text(d, (left_x, y_left), 
                  label="IBAN:", text=f"{safe(self.IBAN)}", 
                  font=self._f9, fill=INK, span_tag=span_tags.IBAN)
        y_left += mm(4)
        self._text(d, (left_x, y_left), 
                  label="BIC: ",
                  text=f"{safe(self.bank_account.BIC)}", 
                  font=self._f9, fill=INK, span_tag=span_tags.BIC)
        y_left += mm(8)
        
        # Delivery address
        self._text(d, (left_x, y_left), text="Konečný příjemce:", font=self._f9, fill=INK)
        y_left += mm(4)
        delivery_text = safe(self.delivery_address) if hasattr(self, 'delivery_address') else "Same as billing"
        self._text(d, (left_x, y_left), text=delivery_text, font=self._f9, fill=INK)

        # Right column - Customer and dates
        self._text(d, (right_x, y), text="Objednávka:", font=self._f11b, fill=INK)
        y_right = y + mm(5)
        
        # Order number
        self._text(d, (right_x, y_right), text="č.", font=self._f9, fill=INK)
        self._text(d, (right_x + mm(10), y_right), text=safe(self.invoice_number), 
                  font=self._f9b, fill=INK, span_tag=span_tags.INVOICE_NUMBER)
        self._text(d, (right_x + mm(40), y_right), text="ze dne", font=self._f9, fill=INK)
        self._text(d, (right_x + mm(52), y_right), text=safe(self.issue_date), 
                  font=self._f9b, fill=INK, span_tag=span_tags.ISSUE_DATE)
        y_right += mm(5)
        
        # Variable symbol
        self._text(d, (right_x, y_right), text="Variabilní symbol:", font=self._f9, fill=INK)
        self._text(d, (right_x + mm(30), y_right), text=safe(self.variable_symbol), 
                  font=self._f9b, fill=INK, span_tag=span_tags.VARIABLE_SYMBOL)
        y_right += mm(5)
        
        # Payment method
        self._text(d, (right_x, y_right), text="Způsob platby:", font=self._f9, fill=INK)
        self._text(d, (right_x + mm(30), y_right), text=safe(self.payment_type), 
                  font=self._f9b, fill=INK, span_tag=span_tags.PAYMENT_TYPE)
        y_right += mm(10)

        # Customer billing info box
        d.rectangle((right_x, y_right, right_x + col_w, y_right + mm(35)), 
                   outline=LINE_MID, width=2, fill=BG)
        
        inner_x = right_x + mm(3)
        inner_y = y_right + mm(3)
        
        self._text(d, (inner_x, inner_y), text="Odběratel:", font=self._f10b, fill=INK)
        inner_y += mm(6)
        self._text(d, (inner_x, inner_y), text=safe(self.customer.name), font=self._f10, fill=INK)
        inner_y += mm(5)
        self._text(d, (inner_x, inner_y), text=safe(self.customer.address), font=self._f10, fill=INK)
        inner_y += mm(5)
        self._text(d, (inner_x, inner_y), text="Česká republika", font=self._f10, fill=INK)
        
        y_right += mm(40)
        
        # Dates
        self._text(d, (right_x, y_right), text="Datum vystavení:", font=self._f9, fill=INK)
        self._text(d, (right_x + mm(35), y_right), text=safe(self.issue_date), 
                  font=self._f9b, fill=INK, span_tag=span_tags.ISSUE_DATE)
        y_right += mm(5)
        
        self._text(d, (right_x, y_right), text="Datum splatnosti:", font=self._f9, fill=INK)
        self._text(d, (right_x + mm(35), y_right), text=safe(self.due_date), 
                  font=self._f9b, fill=INK, span_tag=span_tags.DUE_DATE)
        y_right += mm(5)
        
        self._text(d, (right_x, y_right), text="Datum uskutečnění zdanitelného plnění:", 
                  font=self._f9, fill=INK)
        self._text(d, (right_x + mm(65), y_right), text=safe(self.taxable_supply_date), 
                  font=self._f9b, fill=INK, span_tag=span_tags.TAXABLE_SUPPLY_DATE)

        y = max(y_left, y_right) + mm(10)
        
        # --- ITEMS TABLE ---
        hr(y, "strong")
        y += mm(5)
        
        headers = ["Kód", "Položka", "Počet", "Cena\nbez DPH", "Sleva", "Částka\nbez DPH", "DPH", "Celkem sDPH"]
        col_ws = [0.10, 0.30, 0.08, 0.12, 0.08, 0.12, 0.08, 0.12]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin_l]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        # Table header
        head_h = mm(10)
        baseline = y + mm(2)
        for i, h in enumerate(headers):
            if i in (0, 1):
                self._text(d, (x_cols[i] + 3, baseline), h, font=self._f9b, fill=INK, must_have_same_width=True)
            else:
                self._draw_center(d, x_cols[i] + col_abs[i] / 2, baseline, h, self._f9b, INK, must_have_same_width=True)
        y += head_h
        hr(y, "strong")

        # Table rows
        row_h = mm(8)
        for idx, it in enumerate(self.items, 1):
            y += row_h
            hr(y, "thin")

            cells = [
                safe(it.code) if hasattr(it, 'code') else f"{idx}.",
                safe(it.description),
                f"{safe(it.quantity)} ks",
                fmt_money(it.ppu),
                f"{safe(it.discount) if hasattr(it, 'discount') else '0'}%",
                fmt_money(it.price_without_vat),
                f"{safe(it.vat_percentage)}%",
                fmt_money(it.price_with_vat),
            ]
            
            y_text = y - row_h + mm(2)
            self._text(d, (x_cols[0] + 3, y_text), cells[0], font=self._f9, fill=INK)
            self._text(d, (x_cols[1] + 3, y_text), cells[1], font=self._f9, fill=INK)
            
            for i in range(2, 8):
                self._draw_center(d, x_cols[i] + col_abs[i] / 2, y_text, cells[i], self._f9, INK)

        # Table footer
        y += mm(3)
        hr(y, "strong")
        y += mm(5)

        # VAT summary table (left side)
        vat_box_w = mm(80)
        vat_headers = ["Sazba DPH", "Základ DPH", "Suma DPH"]
        vat_col_w = vat_box_w / 3
        
        self._draw_center(d, margin_l + vat_col_w * 0.5, y, vat_headers[0], self._f9b, INK)
        self._draw_center(d, margin_l + vat_col_w * 1.5, y, vat_headers[1], self._f9b, INK)
        self._draw_center(d, margin_l + vat_col_w * 2.5, y, vat_headers[2], self._f9b, INK)
        
        y += mm(6)
        hr(y, "mid", margin_l, margin_l + vat_box_w)
        
        for v in self.vat:
            y += mm(5)
            _, percentage_id = self._draw_center(d, margin_l + vat_col_w * 0.5, y, 
                                                f"{safe(v.vat_percentage)}%", self._f9, INK, 
                                                span_tag=span_tags.VAT_PERCENTAGE)
            _, base_id = self._draw_center(d, margin_l + vat_col_w * 1.5, y, 
                                          fmt_money(v.vat_base), self._f9, INK, 
                                          span_tag=span_tags.VAT_BASE)
            _, vat_id = self._draw_center(d, margin_l + vat_col_w * 2.5, y, 
                                         fmt_money(v.vat), self._f9, INK, 
                                         span_tag=span_tags.VAT)
            
            self.append_relationship(GRelationship(None, base_id, percentage_id, relationship_types.BASE_OF))
            self.append_relationship(GRelationship(None, vat_id, percentage_id, relationship_types.VAT_OF))
        
        y += mm(6)
        hr(y, "mid", margin_l, margin_l + vat_box_w)
        
        y += mm(5)
        self._draw_center(d, margin_l + vat_col_w * 0.5, y, "Celkem", self._f9b, INK)
        total_base = sum(float(v.vat_base) for v in self.vat)
        total_vat = sum(float(v.vat) for v in self.vat)
        self._draw_center(d, margin_l + vat_col_w * 1.5, y, fmt_money(total_base), self._f9b, INK)
        self._draw_center(d, margin_l + vat_col_w * 2.5, y, fmt_money(total_vat), self._f9b, INK)

        # Total summary (right side)
        summary_x = self._A4_W_PX - margin_r - mm(60)
        y_summary = y - mm(20)
        
        d.rectangle((summary_x - mm(3), y_summary - mm(3), 
                    self._A4_W_PX - margin_r, y_summary + mm(25)), 
                   outline=LINE_MID, width=2, fill=SUBTLE_BG)
        
        def summary_row(label: str, value: str, y_pos: int, bold: bool = False, tag=span_tags.O, end=None):
            font_l = self._f10b if bold else self._f10
            font_v = self._f10b if bold else self._f10
            self._draw_right(d, summary_x + mm(20), y_pos, label, font_l, INK)
            if not end:
                self._draw_right(d, self._A4_W_PX - margin_r - mm(3), y_pos, value, font_v, INK, 
                           span_tag=tag)
            else:
                self._draw_right(d, self._A4_W_PX - margin_r - mm(3), y_pos, value, font_v, INK, end=end,
                           span_tag=tag)
                
        summary_row("Suma bez DPH", fmt_money(total_base), y_summary)
        summary_row("Suma DPH", fmt_money(total_vat), y_summary + mm(5))
        summary_row("Fakturovaná částka", 
                   f"{fmt_money(self.calculated_total_price)}", 
                   y_summary + mm(10),bold=True,end=f"{self.currency.value if hasattr(self.currency, 'value') else self.currency}", tag=span_tags.TOTAL)
        summary_row("Uhrazeno zálohou", 
                   f"{fmt_money(self.calculated_total_price)} {self.currency.value if hasattr(self.currency, 'value') else self.currency}", 
                   y_summary + mm(15), bold=True)
        summary_row("K úhradě", 
                   "0,00 Kč", 
                   y_summary + mm(20), bold=True)

        y = y + mm(15)
        
        # --- FOOTER ---
        hr(y, "thin")
        y += mm(5)
        
        # Footer message
        footer_msg = f"Tímto nákupem jste právě ušetřili {fmt_money(293.00)} Kč :-)"
        self._text(d, (margin_l, y), footer_msg, font=self._f10b, fill=INK)
        y += mm(8)
        
        # Additional info
        self._text(d, (margin_l, y), 
                  "Jak jste byli spokojení s našimi službami? Ohodnoťte nás!", 
                  font=self._f9, fill=INK)
        y += mm(4)
        self._text(d, (margin_l, y), 
                  "Zkontrolujte, prosím, kompletnost vaší zásilky.", 
                  font=self._f9, fill=INK)
        
        y += mm(10)
        
        # Bottom barcode
        barcode_bottom_x = margin_l
        d.rectangle((barcode_bottom_x, y, barcode_bottom_x + mm(30), y + mm(12)), 
                   outline=LINE, width=2, fill=BG)
        self._draw_center(d, barcode_bottom_x + mm(15), y + mm(5), 
                         safe(self.variable_symbol), self._f10, INK)

        # Apply post-processing
        img = self.post_process(img)

        # Save
        img.save(output_path, format="PNG")
        return True