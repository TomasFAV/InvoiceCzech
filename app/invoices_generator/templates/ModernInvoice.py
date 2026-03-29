from typing import final

from PIL import Image, ImageDraw

from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.invoice.Renderers.TextRenderer import TextRenderer
from common.enumerates.SpanTag import SpanTag

from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money


@final
class ModernInvoice(InvoiceTemplate):
    """Moderní minimalistický design s velkými fonty a čistými liniemi"""
    

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # Větší okraje pro vzdušnější design
        margin_l = mm(20)
        margin_r = mm(20)
        margin_t = mm(20)
        margin_b = mm(20)

        # Světle šedé pozadí
        BG_COLOR = (248, 249, 250)
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG_COLOR)
        invoice.image = img
        d = ImageDraw.Draw(img)

        # Barvy pro moderní design
        PRIMARY_COLOR = (33, 37, 41)
        ACCENT_COLOR = (0, 123, 255)
        LIGHT_GRAY = (108, 117, 125)
        BORDER_COLOR = (206, 212, 218)

        y = margin_t

        # --- HLAVIČKA S BAREVNÝM PRUHEM ---
        header_height = mm(25)
        d.rectangle((0, 0, _A4_W_PX, header_height), fill=ACCENT_COLOR)
        
        # Logo/název vlevo v hlavičce
        textRenderer._text(invoice, d,(margin_l, margin_t), safe(data.supplier.name), font=textRenderer._f20b, fill=(255, 255, 255))
        
        # Číslo faktury vpravo
        title_text = f"FAKTURA #{safe(data.invoice_number)}"
        textRenderer._text_right(invoice, d, _A4_W_PX - margin_r, margin_t, label="FAKTURA #", text=f"{safe(data.invoice_number)}", font=textRenderer._f20b, fill=(255, 255, 255),
                            span_tag=SpanTag.INVOICE_NUMBER)

        y = header_height + mm(15)

        # --- INFORMACE O FAKTUŘE V BOXECH ---
        box_height = mm(35)
        box_width = (_A4_W_PX - margin_l - margin_r - mm(10)) // 2

        # Levý box - dodavatel
        supplier_box = (margin_l, y, margin_l + box_width, y + box_height)
        d.rectangle(supplier_box, fill=(255, 255, 255), outline=BORDER_COLOR, width=2)
        
        textRenderer._text(invoice, d,(margin_l + mm(5), y + mm(3)), "DODAVATEL", font=textRenderer._f12b, fill=LIGHT_GRAY)
        textRenderer._text(invoice, d,(margin_l + mm(5), y + mm(8)), safe(data.supplier.name), font=textRenderer._f14b, fill=PRIMARY_COLOR)
        textRenderer._text(invoice, d,(margin_l + mm(5), y + mm(13)), safe(data.supplier.address), font=textRenderer._f11, fill=PRIMARY_COLOR)
        textRenderer._text(invoice, d,(margin_l + mm(5), y + mm(18)), label="IČ: ", text=f"{safe(data.supplier.register_id)}", font=textRenderer._f11, fill=PRIMARY_COLOR,
                    span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        textRenderer._text(invoice, d,(margin_l + mm(5), y + mm(23)), label="DIČ: ", text=f"{safe(data.supplier.tax_id)}", font=textRenderer._f11, fill=PRIMARY_COLOR, span_tag=SpanTag.SUPPLIER_TAX_ID)

        # Pravý box - odběratel
        customer_box = (margin_l + box_width + mm(10), y, _A4_W_PX - margin_r, y + box_height)
        d.rectangle(customer_box, fill=(255, 255, 255), outline=BORDER_COLOR, width=2)
        
        customer_x = margin_l + box_width + mm(15)
        textRenderer._text(invoice, d,(customer_x, y + mm(3)), "ODBĚRATEL", font=textRenderer._f12b, fill=LIGHT_GRAY)
        textRenderer._text(invoice, d,(customer_x, y + mm(8)), safe(data.customer.name), font=textRenderer._f14b, fill=PRIMARY_COLOR)
        textRenderer._text(invoice, d,(customer_x, y + mm(13)), safe(data.customer.address), font=textRenderer._f11, fill=PRIMARY_COLOR)
        if data.customer.register_id:
            textRenderer._text(invoice, d,(customer_x, y + mm(18)), label="IČ: ", text=f"{safe(data.customer.register_id)}", font=textRenderer._f11, fill=PRIMARY_COLOR,
                        span_tag=SpanTag.CUSTOMER_REGISTER_ID)
        if data.customer.tax_id:
            textRenderer._text(invoice, d,(customer_x, y + mm(23)), label="DIČ:", text= f"{safe(data.customer.tax_id)}", font=textRenderer._f11, fill=PRIMARY_COLOR,
                        span_tag=SpanTag.CUSTOMER_TAX_ID)

        y += box_height + mm(15)

        # --- DETAILY FAKTURY ---
        details_y = y
        textRenderer._text(invoice, d,(margin_l, details_y), "Datum vystavení:", font=textRenderer._f11, fill=LIGHT_GRAY)
        textRenderer._text(invoice, d,(margin_l + mm(35), details_y), safe(data.issue_date), font=textRenderer._f11b, fill=PRIMARY_COLOR, span_tag=SpanTag.ISSUE_DATE)
        
        textRenderer._text(invoice, d,(margin_l, details_y + mm(6)), "Datum splatnosti:", font=textRenderer._f11, fill=LIGHT_GRAY)
        textRenderer._text(invoice, d,(margin_l + mm(35), details_y + mm(6)), safe(data.due_date), font=textRenderer._f11b, fill=PRIMARY_COLOR, span_tag=SpanTag.DUE_DATE)

        # Platební údaje vpravo
        payment_x = _A4_W_PX // 2 + mm(10)
        textRenderer._text(invoice, d,(payment_x, details_y), "Způsob platby:", font=textRenderer._f11, fill=LIGHT_GRAY)
        textRenderer._text(invoice, d,(payment_x + mm(30), details_y), safe(data.payment_type), font=textRenderer._f11b, fill=PRIMARY_COLOR, span_tag=SpanTag.PAYMENT_TYPE)
        
        textRenderer._text(invoice, d,(payment_x, details_y + mm(6)), "Variabilní symbol:", font=textRenderer._f11, fill=LIGHT_GRAY)
        textRenderer._text(invoice, d,(payment_x + mm(30), details_y + mm(6)), safe(data.variable_symbol), font=textRenderer._f11b, fill=PRIMARY_COLOR, span_tag=SpanTag.VARIABLE_SYMBOL)

        y += mm(20)

        # --- TABULKA POLOŽEK ---
        table_start_y = y
        headers = ["Položka", "Množství", "Cena/ks", "Celkem bez DPH", "DPH%", "Celkem s DPH"]
        col_widths = [0.26, 0.1, 0.15, 0.25, 0.08, 0.16]
        table_width = _A4_W_PX - margin_l - margin_r
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin_l + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička tabulky
        header_height = mm(12)
        d.rectangle((margin_l, y, _A4_W_PX - margin_r, y + header_height), fill=ACCENT_COLOR)
        
        for i, header in enumerate(headers):
            text_x = x_cols[i] + mm(3)
            if i > 1:  # Číselné sloupce zarovnáváme doprava
                textRenderer._text_center(invoice, d,  x_cols[i]+col_abs[i]/2, y + mm(3), header, textRenderer._f11b, (255, 255, 255), must_have_same_width=True)
            else:
                textRenderer._text(invoice, d,(text_x, y + mm(3)), header, font=textRenderer._f11b, fill=(255, 255, 255), must_have_same_width=True)

        y += header_height

        # Řádky tabulky
        row_height = mm(10)
        for i, item in enumerate(data.items):
            # Střídavé pozadí řádků
            bg_color = (255, 255, 255) if i % 2 == 0 else (248, 249, 250)
            d.rectangle((margin_l, y, _A4_W_PX - margin_r, y + row_height), fill=bg_color)
            
            # Obsah řádku
            row_data = [
                safe(item.description),
                str(safe(item.quantity)),
                fmt_money(item.ppu),
                fmt_money(item.price_without_vat),
                f"{safe(item.vat_percentage)}%",
                fmt_money(item.price_with_vat)
            ]
            
            for j, r_data in enumerate(row_data):
                text_x = x_cols[j] + mm(3)
                if j > 1:  # Číselné hodnoty doprava
                    text_x = x_cols[j] + col_abs[j] - mm(3)
                    textRenderer._text_right(invoice, d, text_x, y + mm(2.5), r_data, textRenderer._f10, PRIMARY_COLOR)
                else:
                    textRenderer._text(invoice, d,(text_x, y + mm(2.5)), r_data, font=textRenderer._f10, fill=PRIMARY_COLOR)
            
            y += row_height

        # --- CELKOVÁ ČÁSTKA ---
        y += mm(10)
        total_box = (_A4_W_PX - margin_r - mm(60), y, _A4_W_PX - margin_r, y + mm(15))
        d.rectangle(total_box, fill=ACCENT_COLOR)
        
        textRenderer._text_center(invoice, d, total_box[0] + (total_box[2] - total_box[0]) / 2, y + mm(4), 
                        label="CELKEM: ", text=f"{fmt_money(data.calculated_total_price)}", end=f"{data.currency.value}", font=textRenderer._f14b, fill=(255, 255, 255),
                        span_tag=SpanTag.TOTAL, must_have_same_width=True)

        # Uložení
        invoice.image = img
        return True
