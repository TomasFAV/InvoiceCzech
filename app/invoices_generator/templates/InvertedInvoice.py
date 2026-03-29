from datetime import datetime
from typing import final

from PIL import Image, ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.enumerates.SpanTag import SpanTag

from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX, INK, LINE, LINE_STRONG, BG
from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money

@final
class InvertedInvoice(InvoiceTemplate):


    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        margin = mm(25)
        
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        # --- HLAVIČKA A INFO O FAKTUŘE ---
        y = margin
        textRenderer._text(invoice,d,(margin, y), label=f"Faktura / Daňový doklad č.", text=f"{safe(data.invoice_number)}", font=textRenderer._f17b, fill=INK, span_tag=SpanTag.INVOICE_NUMBER)
        
        y += mm(10)
        textRenderer._text(invoice,d,(margin, y), label="Datum vystavení:", text=f"{safe(data.issue_date)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.ISSUE_DATE)
        textRenderer._text(invoice,d,(margin, y + mm(5)), label=f"Datum splatnosti:", text=f"{safe(data.due_date)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.DUE_DATE)
        textRenderer._text(invoice,d,(margin, y + mm(10)), label=f"Způsob úhrady: ", text=f"{safe(data.payment_type)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.PAYMENT_TYPE)
        textRenderer._text(invoice,d,(margin, y + mm(15)), label=f"Variabilní symbol:", text=f"{safe(data.variable_symbol)}", font=textRenderer._f11b, fill=INK, span_tag=SpanTag.VARIABLE_SYMBOL)

        # Adresy v bloku vpravo
        address_block_x = _A4_W_PX - margin - mm(80)
        y_address = margin + mm(10)
        textRenderer._text(invoice,d,(address_block_x, y_address), "DODAVATEL:", font=textRenderer._f12b, fill=INK)
        y_address += mm(6)
        textRenderer._text(invoice,d,(address_block_x, y_address), safe(data.supplier.name), font=textRenderer._f11b, fill=INK)
        y_address += mm(5)
        textRenderer._text(invoice,d,(address_block_x, y_address), safe(data.supplier.address), font=textRenderer._f11, fill=INK)
        y_address += mm(5)
        x_end, _ = textRenderer._text(invoice,d,(address_block_x, y_address), label="IČ:",text=f"{safe(data.supplier.register_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        textRenderer._text(invoice,d,(x_end, y_address), label="| DIČ:",text=f"{safe(data.supplier.tax_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.SUPPLIER_TAX_ID)
        
        y_address += mm(10)
        textRenderer._text(invoice,d,(address_block_x, y_address), "ODBĚRATEL:", font=textRenderer._f12b, fill=INK)
        y_address += mm(6)
        textRenderer._text(invoice,d,(address_block_x, y_address), safe(data.customer.name), font=textRenderer._f11b, fill=INK)
        y_address += mm(5)
        textRenderer._text(invoice,d,(address_block_x, y_address), safe(data.customer.address), font=textRenderer._f11, fill=INK)
        y_address += mm(5)
        x_end, _ = textRenderer._text(invoice,d,(address_block_x, y_address), label="IČ: ", text=f"{safe(data.customer.register_id)}", font=textRenderer._f11, fill=INK,
                            span_tag=SpanTag.CUSTOMER_REGISTER_ID)
        textRenderer._text(invoice,d,(x_end, y_address), label="DIČ: ", text=f"{safe(data.customer.tax_id)}", font=textRenderer._f11, fill=INK,
                            span_tag=SpanTag.CUSTOMER_TAX_ID)

        y = max(y + mm(25), y_address + mm(10))

        # --- SOUHRN DPH NAD TABULKOU ---
        y += mm(10)
        
        # Levé zarovnání souhrnu
        summary_x = margin
        textRenderer._text(invoice,d,(summary_x, y), "Přehled DPH:", font=textRenderer._f12b, fill=INK)
        y += mm(5)
        
        for v in data.vat:
            x_end, vat_id = textRenderer._text(invoice,d,(summary_x, y), label="Sazba", text=f"{safe(v.vat_percentage)}", end="%",font=textRenderer._f10, fill=INK, span_tag=SpanTag.O)
            x_end, base_id = textRenderer._text(invoice,d,(x_end, y), label="Základ", text=f"{fmt_money(safe(v.vat_base))}", font=textRenderer._f10, fill=INK, span_tag=SpanTag.O)
            x_end, percentage_id = textRenderer._text(invoice,d,(x_end, y), label="DPH", text=f"{fmt_money(safe(v.vat))}",font=textRenderer._f10, fill=INK, span_tag=SpanTag.O)
        

            y += mm(5)

        y += mm(5)
        d.line([(margin, y), (_A4_W_PX - margin, y)], fill=LINE_STRONG, width=2)
        y += mm(5)

        # --- TABULKA POLOŽEK ---
        table_w = _A4_W_PX - 2 * margin
        
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
                textRenderer._text(invoice,d,(x_cols[i] + 6, baseline), h, font=textRenderer._f11b, fill=INK, must_have_same_width=True)
            else:
                textRenderer._text_right(invoice,d, x_cols[i] + col_abs[i] - 6, baseline, h, textRenderer._f11b, fill=INK, must_have_same_width=True)
        
        y += head_h
        d.line([(margin, y), (_A4_W_PX - margin, y)], fill=LINE_STRONG, width=2)
        
        row_h = mm(6.5)
        for it in data.items:
            y += row_h
            d.line([(margin, y), (_A4_W_PX - margin, y)], fill=LINE, width=1)
            
            cells = [
                safe(it.description),
                safe(it.quantity),
                fmt_money(it.ppu),
                fmt_money(it.price_with_vat),
            ]
            
            y_text = y - row_h + mm(2)
            textRenderer._text(invoice,d,(x_cols[0] + 6, y_text), cells[0], font=textRenderer._f11, fill=INK)
            textRenderer._text_right(invoice,d, x_cols[1] + col_abs[1] - 6, y_text, cells[1], textRenderer._f11, fill=INK)
            textRenderer._text_right(invoice,d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], textRenderer._f11, fill=INK)
            textRenderer._text_right(invoice,d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], textRenderer._f11, fill=INK)

        y += mm(5)
        
        # --- CELKOVÁ SUMA V PRAVÉM DOLNÍM ROHU ---
        total_box_x = _A4_W_PX - margin - mm(70)
        total_box_w = mm(70)
        y_total = y + mm(10)
        
        textRenderer._text(invoice,d,(total_box_x, y_total), "Celkem k úhradě:", font=textRenderer._f13b, fill=INK)
        textRenderer._text_right(invoice,d, total_box_x + total_box_w, y_total,text=f"{fmt_money(data.calculated_total_price)}", end=f"{data.currency.value}", font=textRenderer._f13b, fill=INK, span_tag=SpanTag.TOTAL)

        # --- PATIČKA ---
        footer_y = _A4_H_PX - mm(30)
        d.line([(margin, footer_y), (_A4_W_PX - margin, footer_y)], fill=LINE_STRONG, width=2)
        footer_y += mm(5)
        
        textRenderer._text(invoice,d,(margin, footer_y), "Platbu prosím proveďte na výše uvedený bankovní účet.", font=textRenderer._f11, fill=INK)
        textRenderer._text_right(invoice,d, _A4_W_PX - margin, footer_y, f"Datum tisku: {datetime.now().strftime('%d.%m.%Y')}", font=textRenderer._f11, fill=INK)
        
        invoice.image = img
        return True
