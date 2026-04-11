from typing import final

from PIL import Image, ImageDraw
from decimal import ROUND_HALF_UP


from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.enumerates.SpanTag import SpanTag

from common.utils.consts import _A4_H_PX, _A4_W_PX, INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from common.utils.utilities import mm
from common.utils.utilities import safe, fmt_money


@final
class MartinusInvoice(InvoiceTemplate):

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # Margins
        margin_l = mm(20)
        margin_r = mm(20)
        margin_t = mm(15)
        margin_b = mm(15)

        # Canvas
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        # Helper function for horizontal lines
        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = _A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        y = margin_t

        # --- TOP SECTION WITH BARCODE AND SHIPPING INFO ---
        # Left side - Barcode and ZAS label
        barcode_x = margin_l
        textRenderer._text(invoice, (barcode_x, y), text="ZAS", font=textRenderer._f16b, fill=INK)
        y_barcode = y + mm(8)
        
        # Draw barcode placeholder
        barcode_w = mm(25)
        barcode_h = mm(15)
        d.rectangle((barcode_x, y_barcode, barcode_x + barcode_w, y_barcode + barcode_h), 
                   outline=LINE, width=2, fill=BG)
        
        # Order number below barcode
        y_order = y_barcode + barcode_h + mm(3)
        textRenderer._text(invoice, (barcode_x, y_order), text=safe(data.variable_symbol), 
                  font=textRenderer._f13b, fill=INK, span_tag=SpanTag.VARIABLE_SYMBOL)
        
        # Another barcode below
        y_barcode2 = y_order + mm(8)
        d.rectangle((barcode_x, y_barcode2, barcode_x + barcode_w, y_barcode2 + barcode_h), 
                   outline=LINE, width=2, fill=BG)

        # Right side - Package number and logo
        package_x = _A4_W_PX - margin_r - mm(80)
        d.rectangle((package_x - mm(5), y, package_x + mm(50), y + mm(15)), 
                   outline=LINE, width=2, fill=BG)
        textRenderer._text_center(invoice, package_x + mm(22), y + mm(6), 
                         text=safe(data.variable_symbol), font=textRenderer._f17b, fill=INK,
                         span_tag=SpanTag.VARIABLE_SYMBOL)
        
        # Invoice type label
        y_type = y + mm(17)
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, y_type, 
                        text="FAKTURA", font=textRenderer._f10, fill=INK)
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, y_type + mm(4), 
                        text=safe(data.invoice_number), font=textRenderer._f10b, fill=INK,
                        span_tag=SpanTag.INVOICE_NUMBER)
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, y_type + mm(8), 
                        text="Daňový doklad", font=textRenderer._f9, fill=MUTED)

        # Shipping address in left section
        y_ship = y_barcode + mm(2)
        ship_x = barcode_x + barcode_w + mm(10)
        textRenderer._text(invoice, (ship_x, y_ship), text="Tel na zákazníka:", 
                  font=textRenderer._f9, fill=MUTED)
        textRenderer._text(invoice, (ship_x + mm(25), y_ship), text=safe(data.customer.phone) if hasattr(data.customer, 'phone') else "", 
                  font=textRenderer._f9b, fill=INK)
        
        y_ship += mm(6)
        textRenderer._text(invoice, (ship_x, y_ship), text=safe(data.customer.name), 
                  font=textRenderer._f11b, fill=INK)
        y_ship += mm(5)
        textRenderer._text(invoice, (ship_x, y_ship), text=safe(data.customer.address), 
                  font=textRenderer._f11, fill=INK)

        # Logo martinus.cz
        logo_y = y + mm(35)
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, logo_y, 
                        text="martinus.cz", font=textRenderer._f20b, fill=INK)

        y = logo_y + mm(15)
        
        # --- MAIN INFO SECTION ---
        hr(y, "strong")
        y += mm(8)

        # Two column layout
        col_gap = mm(15)
        table_w = _A4_W_PX - margin_l - margin_r
        col_w = (table_w - col_gap) // 2
        left_x = margin_l
        right_x = margin_l + col_w + col_gap

        # Left column - Supplier (Prodávající)
        textRenderer._text(invoice, (left_x, y), text="Prodávající:", font=textRenderer._f11b, fill=INK)
        y_left = y + mm(5)
        
        textRenderer._text(invoice, (left_x, y_left), text=safe(data.supplier.name), font=textRenderer._f10, fill=INK)
        y_left += mm(4)
        textRenderer._text(invoice, (left_x, y_left), text=safe(data.supplier.address), font=textRenderer._f10, fill=INK)
        y_left += mm(8)
        
        textRenderer._text(invoice, (left_x, y_left), text=f"Tel.: {safe(data.supplier.phone) if hasattr(data.supplier, 'phone') else ''}", 
                  font=textRenderer._f9, fill=INK)
        y_left += mm(4)
        textRenderer._text(invoice, (left_x, y_left), text=f"E-mail: {safe(data.supplier.email) if hasattr(data.supplier, 'email') else ''}", 
                  font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (left_x + mm(20), y_left), text=f"Web: {safe(data.supplier.website) if hasattr(data.supplier, 'website') else ''}", 
                  font=textRenderer._f9, fill=INK)
        y_left += mm(8)
        
        textRenderer._text(invoice, (left_x, y_left), text="IČO:", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (left_x + mm(10), y_left), text=safe(data.supplier.register_id), 
                  font=textRenderer._f9b, fill=INK, span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        textRenderer._text(invoice, (left_x + mm(30), y_left), text="DIČ:", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (left_x + mm(40), y_left), text=safe(data.supplier.tax_id), 
                  font=textRenderer._f9b, fill=INK, span_tag=SpanTag.SUPPLIER_TAX_ID)
        textRenderer._text(invoice, (left_x + mm(60), y_left), text="IČ DPH:", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (left_x + mm(75), y_left), text=safe(data.supplier.vat_id) if hasattr(data.supplier, 'vat_id') else "", 
                  font=textRenderer._f9b, fill=INK)
        y_left += mm(8)
        
        textRenderer._text(invoice, (left_x, y_left), text="Bank account details:", font=textRenderer._f9, fill=INK)
        y_left += mm(4)
        textRenderer._text(invoice, (left_x, y_left),
                    label="Číslo účtu:", 
                    text=f"{safe(data.bank_account_number)}", 
                    font=textRenderer._f9b, fill=INK, span_tag=SpanTag.BANK_ACCOUNT_NUMBER)
        y_left += mm(4)
        textRenderer._text(invoice, (left_x, y_left), 
                  label="IBAN:", text=f"{safe(data.IBAN)}", 
                  font=textRenderer._f9, fill=INK, span_tag=SpanTag.IBAN)
        y_left += mm(4)
        textRenderer._text(invoice, (left_x, y_left), 
                  label="BIC: ",
                  text=f"{safe(data.bank_account.BIC)}", 
                  font=textRenderer._f9, fill=INK, span_tag=SpanTag.BIC)
        y_left += mm(8)
        
        # Delivery address
        textRenderer._text(invoice, (left_x, y_left), text="Konečný příjemce:", font=textRenderer._f9, fill=INK)
        y_left += mm(4)
        delivery_text = safe(data.delivery_address) if hasattr(data, 'delivery_address') else "Same as billing"
        textRenderer._text(invoice, (left_x, y_left), text=delivery_text, font=textRenderer._f9, fill=INK)

        # Right column - Customer and dates
        textRenderer._text(invoice, (right_x, y), text="Objednávka:", font=textRenderer._f11b, fill=INK)
        y_right = y + mm(5)
        
        # Order number
        textRenderer._text(invoice, (right_x, y_right), text="č.", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (right_x + mm(10), y_right), text=safe(data.invoice_number), 
                  font=textRenderer._f9b, fill=INK, span_tag=SpanTag.INVOICE_NUMBER)
        textRenderer._text(invoice, (right_x + mm(40), y_right), text="ze dne", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (right_x + mm(52), y_right), text=safe(data.issue_date), 
                  font=textRenderer._f9b, fill=INK, span_tag=SpanTag.ISSUE_DATE)
        y_right += mm(5)
        
        # Variable symbol
        textRenderer._text(invoice, (right_x, y_right), text="Variabilní symbol:", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (right_x + mm(30), y_right), text=safe(data.variable_symbol), 
                  font=textRenderer._f9b, fill=INK, span_tag=SpanTag.VARIABLE_SYMBOL)
        y_right += mm(5)
        
        # Payment method
        textRenderer._text(invoice, (right_x, y_right), text="Způsob platby:", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (right_x + mm(30), y_right), text=safe(data.payment_type), 
                  font=textRenderer._f9b, fill=INK, span_tag=SpanTag.PAYMENT_TYPE)
        y_right += mm(10)

        # Customer billing info box
        d.rectangle((right_x, y_right, right_x + col_w, y_right + mm(35)), 
                   outline=LINE_MID, width=2, fill=BG)
        
        inner_x = right_x + mm(3)
        inner_y = y_right + mm(3)
        
        textRenderer._text(invoice, (inner_x, inner_y), text="Odběratel:", font=textRenderer._f10b, fill=INK)
        inner_y += mm(6)
        textRenderer._text(invoice, (inner_x, inner_y), text=safe(data.customer.name), font=textRenderer._f10, fill=INK)
        inner_y += mm(5)
        textRenderer._text(invoice, (inner_x, inner_y), text=safe(data.customer.address), font=textRenderer._f10, fill=INK)
        inner_y += mm(5)
        textRenderer._text(invoice, (inner_x, inner_y), text="Česká republika", font=textRenderer._f10, fill=INK)
        
        y_right += mm(40)
        
        # Dates
        textRenderer._text(invoice, (right_x, y_right), text="Datum vystavení:", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (right_x + mm(35), y_right), text=safe(data.issue_date), 
                  font=textRenderer._f9b, fill=INK, span_tag=SpanTag.ISSUE_DATE)
        y_right += mm(5)
        
        textRenderer._text(invoice, (right_x, y_right), text="Datum splatnosti:", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (right_x + mm(35), y_right), text=safe(data.due_date), 
                  font=textRenderer._f9b, fill=INK, span_tag=SpanTag.DUE_DATE)
        y_right += mm(5)
        
        textRenderer._text(invoice, (right_x, y_right), text="Datum uskutečnění zdanitelného plnění:", 
                  font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice, (right_x + mm(65), y_right), text=safe(data.taxable_supply_date), 
                  font=textRenderer._f9b, fill=INK, span_tag=SpanTag.TAXABLE_SUPPLY_DATE)

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
                textRenderer._text(invoice, (x_cols[i] + 3, baseline), h, font=textRenderer._f9b, fill=INK, must_have_same_width=True)
            else:
                textRenderer._text_center(invoice, x_cols[i] + col_abs[i] / 2, baseline, h, textRenderer._f9b, INK, must_have_same_width=True)
        y += head_h
        hr(y, "strong")

        # Table rows
        row_h = mm(8)
        for idx, it in enumerate(data.items, 1):
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
            textRenderer._text(invoice, (x_cols[0] + 3, y_text), cells[0], font=textRenderer._f9, fill=INK)
            textRenderer._text(invoice, (x_cols[1] + 3, y_text), cells[1], font=textRenderer._f9, fill=INK)
            
            for i in range(2, 8):
                textRenderer._text_center(invoice, x_cols[i] + col_abs[i] / 2, y_text, cells[i], textRenderer._f9, INK)

        # Table footer
        y += mm(3)
        hr(y, "strong")
        y += mm(5)

        # VAT summary table (left side)
        vat_box_w = mm(80)
        vat_headers = ["Sazba DPH", "Základ DPH", "Suma DPH"]
        vat_col_w = vat_box_w / 3
        
        textRenderer._text_center(invoice, margin_l + vat_col_w * 0.5, y, vat_headers[0], textRenderer._f9b, INK)
        textRenderer._text_center(invoice, margin_l + vat_col_w * 1.5, y, vat_headers[1], textRenderer._f9b, INK)
        textRenderer._text_center(invoice, margin_l + vat_col_w * 2.5, y, vat_headers[2], textRenderer._f9b, INK)
        
        y += mm(6)
        hr(y, "mid", margin_l, margin_l + vat_box_w)
        
        for v in data.vat:
            y += mm(5)
            _, percentage_id = textRenderer._text_center(invoice, margin_l + vat_col_w * 0.5, y, 
                                                f"{safe(v.vat_percentage)}%", textRenderer._f9, INK, 
                                                span_tag=SpanTag.O)
            _, base_id = textRenderer._text_center(invoice, margin_l + vat_col_w * 1.5, y, 
                                          fmt_money(v.vat_base), textRenderer._f9, INK, 
                                          span_tag=SpanTag.O)
            _, vat_id = textRenderer._text_center(invoice, margin_l + vat_col_w * 2.5, y, 
                                         fmt_money(v.vat), textRenderer._f9, INK, 
                                         span_tag=SpanTag.O)
            

        
        y += mm(6)
        hr(y, "mid", margin_l, margin_l + vat_box_w)
        
        y += mm(5)
        textRenderer._text_center(invoice, margin_l + vat_col_w * 0.5, y, "Celkem", textRenderer._f9b, INK)
        total_base = sum(float(v.vat_base) for v in data.vat)
        total_vat = sum(float(v.vat) for v in data.vat)
        textRenderer._text_center(invoice, margin_l + vat_col_w * 1.5, y, fmt_money(total_base), textRenderer._f9b, INK)
        textRenderer._text_center(invoice, margin_l + vat_col_w * 2.5, y, fmt_money(total_vat), textRenderer._f9b, INK)

        # Total summary (right side)
        summary_x = _A4_W_PX - margin_r - mm(60)
        y_summary = y - mm(20)
        
        d.rectangle((summary_x - mm(3), y_summary - mm(3), 
                    _A4_W_PX - margin_r, y_summary + mm(25)), 
                   outline=LINE_MID, width=2, fill=SUBTLE_BG)
        
        def summary_row(label: str, value: str, y_pos: int, bold: bool = False, tag=SpanTag.O, end=None):
            font_l = textRenderer._f10b if bold else textRenderer._f10
            font_v = textRenderer._f10b if bold else textRenderer._f10
            textRenderer._text_right(invoice, summary_x + mm(20), y_pos, label, font_l, INK)
            if not end:
                textRenderer._text_right(invoice, _A4_W_PX - margin_r - mm(3), y_pos, value, font_v, INK, 
                           span_tag=tag)
            else:
                textRenderer._text_right(invoice, _A4_W_PX - margin_r - mm(3), y_pos, value, font_v, INK, end=end,
                           span_tag=tag)
                
        summary_row("Suma bez DPH", fmt_money(total_base), y_summary)
        summary_row("Suma DPH", fmt_money(total_vat), y_summary + mm(5))
        summary_row("Fakturovaná částka", 
                   f"{fmt_money(data.calculated_total_price)}", 
                   y_summary + mm(10),bold=True,end=f"{data.currency.value if hasattr(data.currency, 'value') else data.currency}", tag=SpanTag.TOTAL)
        summary_row("Uhrazeno zálohou", 
                   f"{fmt_money(data.calculated_total_price)} {data.currency.value if hasattr(data.currency, 'value') else data.currency}", 
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
        textRenderer._text(invoice, (margin_l, y), footer_msg, font=textRenderer._f10b, fill=INK)
        y += mm(8)
        
        # Additional info
        textRenderer._text(invoice, (margin_l, y), 
                  "Jak jste byli spokojení s našimi službami? Ohodnoťte nás!", 
                  font=textRenderer._f9, fill=INK)
        y += mm(4)
        textRenderer._text(invoice, (margin_l, y), 
                  "Zkontrolujte, prosím, kompletnost vaší zásilky.", 
                  font=textRenderer._f9, fill=INK)
        
        y += mm(10)
        
        # Bottom barcode
        barcode_bottom_x = margin_l
        d.rectangle((barcode_bottom_x, y, barcode_bottom_x + mm(30), y + mm(12)), 
                   outline=LINE, width=2, fill=BG)
        textRenderer._text_center(invoice, barcode_bottom_x + mm(15), y + mm(5), 
                         safe(data.variable_symbol), textRenderer._f10, INK)

        # Save
        invoice.image = img
        return True