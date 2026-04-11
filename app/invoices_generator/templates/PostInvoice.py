from typing import final

from PIL import Image, ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.enumerates.SpanTag import SpanTag

from common.utils.consts import _A4_H_PX, _A4_W_PX, INK, LINE_STRONG, BG
from common.utils.utilities import mm
from common.utils.utilities import safe, fmt_money


@final
class PostInvoice(InvoiceTemplate):


    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # Okraje
        margin_l = mm(15)
        margin_r = mm(15)
        margin_t = mm(15)
        margin_b = mm(15)

        # Barvy pro ČP design
        _HEADER_BG = (208, 208, 208)
        _CUSTOMER_BG = (232, 232, 232)
        _CUSTOMER_HEADER_BG = (192, 192, 192)
        _TABLE_HEADER_BG = (240, 240, 240)
        _BORDER = (153, 153, 153)

        # Plátno
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        # Start Y
        y = margin_t

        # --- HLAVIČKA S POZADÍM ---
        header_h = mm(15)
        d.rectangle((margin_l, y, _A4_W_PX - margin_r, y + header_h),
                    fill=_HEADER_BG, outline=_BORDER, width=2)

        # Text hlavičky
        textRenderer._text(invoice,(margin_l + mm(15), y + mm(8)), "Daňový doklad",
                font=textRenderer._f14b, fill=INK)

        # Variabilní symbol vpravo
        vs_x = _A4_W_PX - margin_r - mm(15)
        textRenderer._text_right(invoice, vs_x, y + mm(2), "Variabilní symbol pro platbu", textRenderer._f10, INK)
        textRenderer._text_right(invoice, vs_x, y + mm(8), safe(data.variable_symbol), textRenderer._f14b, INK, span_tag=SpanTag.VARIABLE_SYMBOL)

        y += header_h + mm(15)

        # --- HLAVNÍ SEKCE DVA SLOUPCE ---
        left_col_w = mm(120)
        right_col_w = mm(70)
        left_x = margin_l
        right_x = left_x + left_col_w - mm(10)

        # LEVÝ SLOUPEC - Dodavatel
        y_left = y

        # Číslo faktury
        textRenderer._text(invoice,(left_x, y_left), label="Č.",text=f"{safe(data.invoice_number)}", font=textRenderer._f10b, fill=INK, span_tag=SpanTag.INVOICE_NUMBER)
        y_left += mm(4)
        textRenderer._text(invoice,(left_x, y_left), "- pro účely kontrolního hlášení DPH v ČR",
                font=textRenderer._f8, fill=INK)
        y_left += mm(10)

        # Dodavatel
        textRenderer._text(invoice,(left_x, y_left), "Dodavatel:", font=textRenderer._f10b, fill=INK)
        #y_left += mm(5)

        # Konstantní symbol + ID klienta (pokud máš)
        textRenderer._text(invoice,(left_x+mm(50), y_left), label="Konstantní symbol: ", text=f"{safe(data.const_symbol)}", font=textRenderer._f10b, fill=INK,
                    span_tag=SpanTag.CONST_SYMBOL)
        y_left += mm(5)

        textRenderer._text(invoice,(left_x, y_left), f"{safe(data.supplier.name)} {safe(data.supplier.type.value)}, {safe(data.supplier.street)}", font=textRenderer._f11b, fill=INK)
        y_left += mm(5)
        textRenderer._text(invoice,(left_x, y_left), f"{safe(data.supplier.zip)} {safe(data.supplier.city)}", font=textRenderer._f10, fill=INK)
        y_left += mm(5)

        x_supp, _ =textRenderer._text(invoice,(left_x, y_left), label="DIČ: ", text=f"{safe(data.supplier.tax_id)}", font=textRenderer._f10, fill=INK, span_tag=SpanTag.SUPPLIER_TAX_ID)
        textRenderer._text(invoice,(x_supp, y_left), label="IČ: ", text=f"{safe(data.supplier.register_id)}", font=textRenderer._f10, fill=INK, span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        y_left += mm(5)



        # Bankovní informace
        # Pokusíme se vytáhnout dostupná pole z data.bank_account
        bank_name = safe(data.bank_account.name)
        acc_num = safe(getattr(data, "bank_account_number", ""))
        bic = safe(getattr(data.bank_account, "BIC", ""))

        
        textRenderer._text(invoice,(left_x, y_left), label=f"IBAN: ", text=f"{data.IBAN}", font=textRenderer._f10b, fill=INK, span_tag=SpanTag.IBAN)
        y_left += mm(5)
        textRenderer._text(invoice,(left_x, y_left), label="SWIFT/BIC: ", text=f"{bic}", font=textRenderer._f10b, fill=INK, span_tag=SpanTag.BIC)
        y_left += mm(15)

        # Dvojice „Peněžní ústav / Číslo účtu“
        textRenderer._text(invoice,(left_x, y_left), "Peněžní ústav:", font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice,(left_x + mm(50), y_left), "Číslo účtu:", font=textRenderer._f9, fill=INK)
        y_left += mm(5)
        textRenderer._text(invoice,(left_x, y_left), safe(bank_name), font=textRenderer._f9, fill=INK)
        textRenderer._text(invoice,(left_x + mm(50), y_left), text=safe(acc_num), font=textRenderer._f9, fill=INK, span_tag=SpanTag.BANK_ACCOUNT_NUMBER)
        y_left += mm(15)

        # PRAVÝ SLOUPEC - Odběratel
        customer_h = mm(50)
        d.rectangle((right_x, y, right_x + right_col_w, y + customer_h),
                    fill=_CUSTOMER_BG, outline=_BORDER, width=2)

        # Hlavička odběratele
        d.rectangle((right_x, y, right_x + right_col_w, y + mm(10)),
                    fill=_CUSTOMER_HEADER_BG, outline=_BORDER, width=1)
        textRenderer._text(invoice,(right_x + mm(8), y + mm(5)), "ODBĚRATEL",
                font=textRenderer._f10b, fill=INK)

        # Údaje odběratele
        customer_y = y + mm(12)
        textRenderer._text(invoice,(right_x + mm(3), customer_y), safe(data.customer.name),
                font=textRenderer._f12b, fill=INK)
        customer_y += mm(8)
        textRenderer._text(invoice,(right_x + mm(3), customer_y), safe(data.customer.address),
                font=textRenderer._f10, fill=INK)
        customer_y += mm(8)
        x_cust, _ = textRenderer._text(invoice,(right_x + mm(3), customer_y),
                label="IČ:", text=f"{safe(data.customer.register_id)}", end=",",
                font=textRenderer._f10, fill=INK, span_tag=SpanTag.CUSTOMER_REGISTER_ID)
        customer_y += mm(4)

        textRenderer._text(invoice,(right_x + mm(3), customer_y),
                label="DIČ:", text=f"{safe(data.customer.tax_id)}", end=",",
                font=textRenderer._f10, fill=INK, span_tag=SpanTag.CUSTOMER_TAX_ID)
        

        # QR kód placeholder (případně sem můžeš vygenerovat skutečný QR)
        qr_size = mm(15)
        qr_x = right_x + right_col_w - mm(20)
        qr_y = y + customer_h + mm(5)
        d.rectangle((qr_x, qr_y, qr_x + qr_size, qr_y + qr_size),
                    fill=(240, 240, 240), outline=_BORDER, width=2)
        textRenderer._text_center(invoice, qr_x + qr_size/2, qr_y + qr_size/2 - mm(2),
                        "QR", textRenderer._f8, (102, 102, 102))

        y += customer_h + mm(30)

        # --- DATUMY A ÚDAJE ---
        dates_h = mm(25)
        table_w = _A4_W_PX - margin_l - margin_r

        pay_str = safe(data.payment_type)
        curr_str = data.currency.value if hasattr(data.currency, "value") else str(data.currency)

        dates_data = [
            ("Datum vystavení daňového dokladu", safe(data.issue_date), "Den splatnosti", safe(data.due_date), SpanTag.ISSUE_DATE, SpanTag.DUE_DATE),
            ("Datum uskutečnění zdanitelného plnění", safe(data.taxable_supply_date), "Forma úhrady", pay_str, SpanTag.TAXABLE_SUPPLY_DATE, SpanTag.PAYMENT_TYPE),
            ("", "", "Měna", curr_str, SpanTag.O, SpanTag.O)
        ]

        for i, (label1, val1, label2, val2, tag1, tag2) in enumerate(dates_data):
            row_y = y + i * mm(8)
            d.line([(margin_l, row_y + mm(6)), (_A4_W_PX - margin_r, row_y + mm(6))],
                    fill=(204, 204, 204), width=1)

            if label1:
                textRenderer._text(invoice,(margin_l, row_y), label1, font=textRenderer._f10b, fill=INK)
                textRenderer._text(invoice,(margin_l + mm(70), row_y), safe(val1), font=textRenderer._f10b, fill=INK, span_tag=tag1)

            if label2:
                textRenderer._text(invoice,(margin_l + mm(105), row_y), label2, font=textRenderer._f10b, fill=INK)
                textRenderer._text(invoice,(margin_l + mm(140), row_y), safe(val2), font=textRenderer._f10b, fill=INK, span_tag=tag2)

        y += dates_h + mm(10)

        # --- TABULKA POLOŽEK ---
        headers = ["Pol.", "Množství", "Předmět plnění", "Sazba DPH", "Celkem"]
        col_widths = [0.08, 0.20, 0.37, 0.15, 0.20]
        col_abs = [int(w * table_w) for w in col_widths]
        x_cols = [margin_l]
        for w in col_abs[:-1]:
            x_cols.append(x_cols[-1] + w)

        header_h = mm(12)
        d.rectangle((margin_l, y, _A4_W_PX - margin_r, y + header_h),
                    fill=_TABLE_HEADER_BG, outline=_BORDER, width=2)

        # Svislé čáry hlavičky
        for x in x_cols[1:]:
            d.line([(x, y), (x, y + header_h)], fill=_BORDER, width=2)

        # Texty hlavičky
        for i, header in enumerate(headers):
            textRenderer._text_center(invoice, x_cols[i] + col_abs[i]/2, y + mm(5), header, textRenderer._f10b, INK, must_have_same_width=True)

        y += header_h

        # Řádky položek (dynamicky)
        row_h = mm(7)
        for idx, it in enumerate(data.items, start=1):
            d.rectangle((margin_l, y, _A4_W_PX - margin_r, y + row_h),
                        fill=BG, outline=_BORDER, width=2)

            # Svislé čáry
            for x in x_cols[1:]:
                d.line([(x, y), (x, y + row_h)], fill=_BORDER, width=2)

            qty_unit = ""
            if hasattr(it, "quantity"):
                unit = getattr(it, "unit", "ks")
                qty_unit = f"{safe(it.quantity)} {safe(unit)}"

            # Buňky
            textRenderer._text_center(invoice, x_cols[0] + col_abs[0]/2, y + mm(2), f"{idx:03}", textRenderer._f9, INK)  # Pol.
            textRenderer._text_center(invoice, x_cols[1] + col_abs[1]/2, y + mm(2), qty_unit, textRenderer._f9, INK)     # Množství
            textRenderer._text(invoice,(x_cols[2] + mm(2), y + mm(1)), safe(it.description), font=textRenderer._f9, fill=INK)  # Popis
            textRenderer._text_center(invoice, x_cols[3] + col_abs[3]/2, y + mm(2), f"{safe(it.vat_percentage)} %", textRenderer._f9, INK)  # DPH %
            textRenderer._text_right(invoice, x_cols[4] + col_abs[4] - mm(3), y + mm(2), fmt_money(it.price_with_vat), textRenderer._f9, INK)  # Celkem

            y += row_h

        y += mm(10)

        # --- SOUHRN DPH ---
        summary_h = mm(7)
        summary_headers = ["Sazba DPH %", "Základ DPH", "DPH", "Celkem s DPH"]
        summary_widths = [0.20, 0.25, 0.20, 0.25]
        summary_abs = [int(w * table_w) for w in summary_widths]
        summary_x_cols = [margin_l]
        for w in summary_abs[:-1]:
            summary_x_cols.append(summary_x_cols[-1] + w)

        # Hlavička souhrnu
        d.rectangle((margin_l, y, _A4_W_PX - margin_r, y + summary_h),
                    fill=_TABLE_HEADER_BG, outline=_BORDER, width=2)

        for x in summary_x_cols[1:]:
            d.line([(x, y), (x, y + summary_h)], fill=_BORDER, width=2)

        for i, header in enumerate(summary_headers):
            textRenderer._text_center(invoice, summary_x_cols[i] + summary_abs[i]/2, y + mm(3), header, textRenderer._f10b, INK)

        y += summary_h

        # Data souhrnu (dle data.vat)
        for v in data.vat:
            d.rectangle((margin_l, y, _A4_W_PX - margin_r, y + summary_h),
                        fill=BG, outline=_BORDER, width=2)
            for x in summary_x_cols[1:]:
                d.line([(x, y), (x, y + summary_h)], fill=_BORDER, width=2)

            _, percentage_id = textRenderer._text_center(invoice, summary_x_cols[0] + summary_abs[0]/2, y + mm(2),
                            f"{safe(v.vat_percentage)}", textRenderer._f10, INK, span_tag=SpanTag.O)
            _, base_id = textRenderer._text_right(invoice, summary_x_cols[1] + summary_abs[1] - mm(3), y + mm(2),
                            fmt_money(v.vat_base), textRenderer._f10, INK, span_tag=SpanTag.O)
            _, vat_id = textRenderer._text_right(invoice, summary_x_cols[2] + summary_abs[2] - mm(3), y + mm(2),
                            fmt_money(v.vat), textRenderer._f10, INK, span_tag=SpanTag.O)
            textRenderer._text_right(invoice, summary_x_cols[3] + summary_abs[3] - mm(3), y + mm(2),
                            fmt_money(float(v.vat_base) + float(v.vat)), textRenderer._f10, INK)
        
            
            y += summary_h

        y += mm(5)

        # --- CELKOVÉ ČÁSTKY ---
        d.line([(margin_l, y), (_A4_W_PX - margin_r, y)], fill=LINE_STRONG, width=2)
        y += mm(3)

        textRenderer._text(invoice,(margin_l, y), "Celkem", font=textRenderer._f12b, fill=INK)
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, y, text=fmt_money(data.calculated_total_price), font=textRenderer._f12b, fill=INK, span_tag=SpanTag.TOTAL)
        y += mm(8)

        d.line([(margin_l, y), (_A4_W_PX - margin_r, y)], fill=LINE_STRONG, width=2)
        y += mm(3)

        textRenderer._text(invoice,(margin_l, y), "Celkem k úhradě", font=textRenderer._f12b, fill=INK)
        textRenderer._text_right(invoice,
            _A4_W_PX - margin_r,
            y,
            text=f"{fmt_money(data.calculated_total_price)}",
            font=textRenderer._f12b,
            fill=INK,
            span_tag=SpanTag.TOTAL)


        invoice.image = img
        return True
