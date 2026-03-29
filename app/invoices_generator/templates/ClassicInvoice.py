from typing import final

from PIL import Image, ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.enumerates.SpanTag import SpanTag

from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX
from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money

@final
class ClassicInvoice(InvoiceTemplate):
    """Klasická faktura s tradičním layoutem a černobílým designem"""



    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # Standardní okraje
        margin_l = mm(15)
        margin_r = mm(15)
        margin_t = mm(15)
        margin_b = mm(15)

        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), (255, 255, 255))
        invoice.image = img
        d = ImageDraw.Draw(img)

        # Černobílé barvy
        BLACK = (0, 0, 0)
        GRAY = (128, 128, 128)
        LIGHT_GRAY = (200, 200, 200)

        y = margin_t

        # --- HLAVIČKA ---
        # Dvojitá linie nahoře
        d.line([(margin_l, y), (_A4_W_PX - margin_r, y)], fill=BLACK, width=3)
        d.line([(margin_l, y + 3), (_A4_W_PX - margin_r, y + 3)], fill=BLACK, width=1)
        
        y += mm(8)
        
        # Název firmy velký font
        textRenderer._text(invoice,d,(margin_l, y), safe(data.supplier.name).upper(), font=textRenderer._f18b, fill=BLACK)
        
        # Faktura vpravo
        textRenderer._text_right(invoice,d, _A4_W_PX - margin_r, y, label="FAKTURA Č. ", text=f"{data.invoice_number}", font=textRenderer._f16b, fill=BLACK, span_tag=SpanTag.INVOICE_NUMBER)
        
        y += mm(12)

        # --- ÚDAJE O FIRMĚ ---
        textRenderer._text(invoice,d,(margin_l, y), f"Sídlo: {safe(data.supplier.address)}", font=textRenderer._f10, fill=BLACK)
        y += mm(5)
        x_dic, _ = textRenderer._text(invoice,d,(margin_l, y), label="IČ: ", text=f"{safe(data.supplier.register_id)}", end="|", font=textRenderer._f10, fill=BLACK, span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        textRenderer._text(invoice,d,(x_dic, y), label="DIČ: ", text=f"{safe(data.supplier.tax_id)}", font=textRenderer._f10, fill=BLACK, span_tag=SpanTag.SUPPLIER_TAX_ID)

        y += mm(10)
        d.line([(margin_l, y), (_A4_W_PX - margin_r, y)], fill=LIGHT_GRAY, width=1)
        y += mm(8)

        # --- ADRESÁT V RÁMEČKU ---
        box_width = mm(80)
        box_height = mm(35)
        d.rectangle((margin_l, y, margin_l + box_width, y + box_height), outline=BLACK, width=2)
        
        # Hlavička rámečku
        d.rectangle((margin_l, y, margin_l + box_width, y + mm(8)), fill=LIGHT_GRAY)
        textRenderer._text(invoice,d,(margin_l + mm(3), y + mm(2)), "FAKTURAČNÍ ADRESA", font=textRenderer._f10b, fill=BLACK)
        
        # Obsah
        content_y = y + mm(12)
        textRenderer._text(invoice,d,(margin_l + mm(3), content_y), safe(data.customer.name), font=textRenderer._f11b, fill=BLACK)
        content_y += mm(5)
        textRenderer._text(invoice,d,(margin_l + mm(3), content_y), safe(data.customer.address), font=textRenderer._f10, fill=BLACK)
        content_y += mm(5)
        if data.customer.register_id:
            textRenderer._text(invoice,d,(margin_l + mm(3), content_y), label="IČ: ", text=f"{safe(data.customer.register_id)}", font=textRenderer._f10, fill=BLACK, span_tag=SpanTag.CUSTOMER_REGISTER_ID)
            content_y += mm(4)
        if data.customer.tax_id:
            textRenderer._text(invoice,d,(margin_l + mm(3), content_y), label="DIČ: ", text=f"{safe(data.customer.tax_id)}", font=textRenderer._f10, fill=BLACK, span_tag=SpanTag.CUSTOMER_TAX_ID)

        # --- ÚDAJE O FAKTUŘE VPRAVO ---
        info_x = margin_l + box_width + mm(20)
        info_y = y
        
        textRenderer._text(invoice,d,(info_x, info_y), "ÚDAJE O FAKTUŘE", font=textRenderer._f12b, fill=BLACK)
        info_y += mm(8)
        
        d.line([(info_x, info_y), (_A4_W_PX - margin_r, info_y)], fill=BLACK, width=1)
        info_y += mm(5)
        
        # Tabulka údajů
        label_width = mm(35)
        labels_values = [
            ("Datum vystavení:", safe(data.issue_date), SpanTag.ISSUE_DATE),
            ("Datum zdaň. plnění:", safe(data.taxable_supply_date), SpanTag.TAXABLE_SUPPLY_DATE),
            ("Datum splatnosti:", safe(data.due_date), SpanTag.DUE_DATE),
            ("Způsob úhrady:", safe(data.payment_type), SpanTag.PAYMENT_TYPE),
            ("Variabilní symbol:", safe(data.variable_symbol), SpanTag.VARIABLE_SYMBOL),
        ]
        
        for label, value, tag in labels_values:
            textRenderer._text(invoice,d,(info_x, info_y), label, font=textRenderer._f10, fill=BLACK)
            textRenderer._text(invoice,d,(info_x + label_width, info_y), value, font=textRenderer._f10b, fill=BLACK, span_tag=tag)
            info_y += mm(5)

        y = max(y + box_height + mm(15), info_y + mm(10))

        # --- TABULKA POLOŽEK ---
        # Hlavička tabulky
        table_y = y
        headers = ["č.", "Popis zboží/služby", "MJ", "Množství", "Cena bez DPH", "DPH %", "Cena s DPH"]
        col_widths = [0.05, 0.25, 0.05, 0.10, 0.25, 0.08, 0.22]
        table_width = _A4_W_PX - margin_l - margin_r
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin_l + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička s tmavým pozadím
        header_height = mm(8)
        d.rectangle((margin_l, y, _A4_W_PX - margin_r, y + header_height), fill=GRAY)
        
        for i, header in enumerate(headers):
            if i in [0, 3,4, 5,6]:  # Číslo, množství, DPH% - střed
                textRenderer._text_center(invoice,d, x_cols[i] + col_abs[i] // 2, y + mm(2), header, textRenderer._f9b, (255, 255, 255), must_have_same_width=True)
            else:  # Popis, MJ - vlevo
                textRenderer._text(invoice,d,(x_cols[i] + mm(2), y + mm(2)), header, font=textRenderer._f9b, fill=(255, 255, 255), must_have_same_width=True)

        y += header_height

        # Řádky tabulky
        row_height = mm(7)
        for idx, item in enumerate(data.items, 1):
            # Ohraničení řádku
            d.line([(margin_l, y + row_height), (_A4_W_PX - margin_r, y + row_height)], fill=LIGHT_GRAY, width=1)
            
            row_data = [
                str(idx),
                safe(item.description),
                "ks",  # jednotka
                str(safe(item.quantity)),
                fmt_money(item.price_without_vat),
                f"{safe(item.vat_percentage)}%",
                fmt_money(item.price_with_vat)
            ]
            
            for i, r_data in enumerate(row_data):
                text_y = y + mm(1.5)
                if i in [0, 3, 5]:  # Střed
                    textRenderer._text_center(invoice,d, x_cols[i] + col_abs[i] // 2, text_y, r_data, textRenderer._f9, BLACK)
                elif i in [4, 6]:  # Doprava
                    textRenderer._text_right(invoice,d, x_cols[i] + col_abs[i] - mm(2), text_y, r_data, textRenderer._f9, BLACK)
                else:  # Vlevo
                    textRenderer._text(invoice,d,(x_cols[i] + mm(2), text_y), r_data, font=textRenderer._f9, fill=BLACK)
            
            y += row_height

        # Silná linka na konci tabulky
        d.line([(margin_l, y), (_A4_W_PX - margin_r, y)], fill=BLACK, width=2)
        
        y += mm(5)

        # --- REKAPITULACE ---
        # Celková částka v rámečku
        total_box_width = mm(50)
        total_box_height = mm(12)
        total_x = _A4_W_PX - margin_r - total_box_width
        
        total_x_end, _ = textRenderer._text_center(invoice,d, total_x + total_box_width // 2, y + mm(3), label="CELKEM K ÚHRADĚ: ", text=f"{fmt_money(data.calculated_total_price)}"
                ,end=f"{data.currency.value}",font=textRenderer._f10b, fill=BLACK, span_tag=SpanTag.TOTAL)

        d.rectangle((total_x, y, total_x_end, y + total_box_height), outline=BLACK, width=2)

        y += total_box_height + mm(15)

        # --- PLATEBNÍ ÚDAJE ---
        textRenderer._text(invoice,d,(margin_l, y), "PLATEBNÍ ÚDAJE", font=textRenderer._f12b, fill=BLACK)
        y += mm(6)
        d.line([(margin_l, y), (margin_l + mm(40), y)], fill=BLACK, width=1)
        y += mm(5)
        
        textRenderer._text(invoice,d,(margin_l, y), label=f"Bankovní spojení:", text=data.bank_account.name, font=textRenderer._f10, fill=BLACK)
        y += mm(4)
        textRenderer._text(invoice,d,(margin_l, y), label="Číslo účtu: ", text=f"{safe(data.bank_account_number)}", font=textRenderer._f10, fill=BLACK, span_tag=SpanTag.BANK_ACCOUNT_NUMBER)
        y += mm(4)
        textRenderer._text(invoice,d,(margin_l, y), label="IBAN", text=f"{safe(data.IBAN)}", font=textRenderer._f10, fill=BLACK, span_tag=SpanTag.IBAN)

        # Uložení
        invoice.image = img
        return True
