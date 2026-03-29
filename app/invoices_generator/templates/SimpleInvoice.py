from datetime import datetime
from typing import final

from PIL import Image, ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.enumerates.SpanTag import SpanTag

from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX, INK, LINE, LINE_MID, LINE_STRONG, BG
from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money


@final
class SimpleInvoice(InvoiceTemplate):

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        margin_l = mm(20)
        margin_r = mm(20)
        margin_t = mm(20)
        
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = _A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        y = margin_t

        # --- ZÁVĚREČNÁ SUMA Nahoře ---
        total_price_x = _A4_W_PX - margin_r - mm(40)
        textRenderer._text(invoice, d,(total_price_x, y), "CELKEM K ZAPLACENÍ", font=textRenderer._f13b, fill=INK)
        y += mm(5)
        textRenderer._text(invoice, d,(total_price_x, y), text=f"{fmt_money(data.calculated_total_price)}", end=f"{data.currency.value}", font=textRenderer._f17b, fill=INK, span_tag=SpanTag.TOTAL)
        
        # Datové pole uprostřed nahoře
        date_box_x = _A4_W_PX / 2
        
        textRenderer._text_center(invoice, d, date_box_x, margin_t, "FAKTURA", textRenderer._f17b, INK)
        textRenderer._text_center(invoice, d, date_box_x, margin_t + mm(8), label=f"Číslo faktury: ", text=f"{safe(data.invoice_number)}", font=textRenderer._f13b, fill=INK,
                            span_tag=SpanTag.INVOICE_NUMBER)
        
        y += mm(15)
        hr(y, "strong")
        y += mm(5)
        
        # --- BLOKY INFORMACÍ PROHOZENÉ ---
        # Bankovní účet a symboly - Nalevo
        bank_x = margin_l
        textRenderer._text(invoice, d,(bank_x, y), "Platební údaje:", font=textRenderer._f12b, fill=INK)
        y += mm(5)
        textRenderer._text(invoice, d,(bank_x, y), label="Bankovní účet:", text=f"{safe(data.bank_account_number)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.BANK_ACCOUNT_NUMBER)
        y += mm(5)
        textRenderer._text(invoice, d,(bank_x, y), label="IBAN: ", text=f"{safe(data.IBAN)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.IBAN)
        y += mm(5)
        textRenderer._text(invoice, d,(bank_x, y), label="Variabilní symbol: ", text=f"{safe(data.variable_symbol)}", font=textRenderer._f11b, fill=INK, span_tag=SpanTag.VARIABLE_SYMBOL)

        # Datové pole - Napravo
        dates_x = _A4_W_PX - margin_r - mm(50)
        textRenderer._text(invoice, d,(dates_x, y - mm(15)), "Datum vystavení:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, d,(dates_x + mm(30), y - mm(15)), safe(data.issue_date), font=textRenderer._f11b, fill=INK, span_tag=SpanTag.ISSUE_DATE)
        
        textRenderer._text(invoice, d,(dates_x, y - mm(10)), "Datum splatnosti:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, d,(dates_x + mm(30), y - mm(10)), safe(data.due_date), font=textRenderer._f11b, fill=INK, span_tag=SpanTag.DUE_DATE)
        
        textRenderer._text(invoice, d,(dates_x, y - mm(5)), "Způsob platby:", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, d,(dates_x + mm(30), y - mm(5)), safe(data.payment_type), font=textRenderer._f11b, fill=INK, span_tag=SpanTag.PAYMENT_TYPE)

        # --- DODAVATEL / ODBĚRATEL VE STŘEDU ---
        y_middle = y + mm(5)
        
        # Dodavatel
        textRenderer._text_center(invoice, d, _A4_W_PX / 2, y_middle, "DODAVATEL", textRenderer._f12b, INK)
        textRenderer._text_center(invoice, d, _A4_W_PX / 2, y_middle + mm(5), safe(data.supplier.name), textRenderer._f11b, INK)
        textRenderer._text_center(invoice, d, _A4_W_PX / 2, y_middle + mm(10), safe(data.supplier.address), textRenderer._f11, INK)
        x_end, _ = textRenderer._text_center(invoice, d, _A4_W_PX / 2, y_middle + mm(15), label=f"IČ: ", text=f"{safe(data.supplier.register_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        textRenderer._text(invoice, d, (x_end, y_middle + mm(15)), label=f"DIČ: ", text=f"{safe(data.supplier.tax_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.SUPPLIER_TAX_ID)
        y = y_middle + mm(25)
        
        # Odběratel
        textRenderer._text_center(invoice, d, _A4_W_PX / 2, y, "ODBĚRATEL", textRenderer._f12b, INK)
        textRenderer._text_center(invoice, d, _A4_W_PX / 2, y + mm(5), safe(data.customer.name), textRenderer._f11b, INK)
        textRenderer._text_center(invoice, d, _A4_W_PX / 2, y + mm(10), safe(data.customer.address), textRenderer._f11, INK)       
        x_end, _ = textRenderer._text_center(invoice, d, _A4_W_PX / 2, y + mm(15), label=f"IČ: ", text=f"{safe(data.customer.register_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.CUSTOMER_REGISTER_ID)
        textRenderer._text(invoice, d, (x_end, y + mm(15)), label=f"DIČ: ", text=f"{safe(data.customer.tax_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.CUSTOMER_TAX_ID)

        y += mm(25)
        hr(y, "strong")
        y += mm(5)
        
        # --- TABULKA POLOŽEK ---
        table_w = _A4_W_PX - 2 * margin_l
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
                textRenderer._text(invoice, d,(x_cols[i] + 6, baseline), h, font=textRenderer._f11b, fill=INK, must_have_same_width=True)
            else:
                textRenderer._text_right(invoice, d, x_cols[i] + col_abs[i] - 6, baseline, h, textRenderer._f11b, INK, must_have_same_width=True)
        
        y += head_h
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)
        
        row_h = mm(6.5)
        for it in data.items:
            y += row_h
            d.line((margin_l, y, margin_l + table_w, y), fill=LINE, width=1)
            
            cells = [
                f"{safe(it.quantity)}x {safe(it.description)}",
                fmt_money(it.ppu),
                f"{safe(it.vat_percentage)}%",
                fmt_money(it.price_with_vat),
            ]
            
            y_text = y - row_h + mm(2)
            textRenderer._text(invoice, d,(x_cols[0] + 6, y_text), cells[0], font=textRenderer._f11, fill=INK)
            textRenderer._text_right(invoice, d, x_cols[1] + col_abs[1] - 6, y_text, cells[1], textRenderer._f11, INK)
            textRenderer._text_right(invoice, d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], textRenderer._f11, INK)
            textRenderer._text_right(invoice, d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], textRenderer._f11, INK)

        y += mm(2)
        hr(y, "strong")
        y += mm(5)

        # --- PATIČKA ---
        
        # QR Kód a poznámky - dole
        qr_size = mm(20)
        qr_x = mm(20)
        qr_y = _A4_H_PX - mm(40)
        d.rectangle((qr_x, qr_y, qr_x + qr_size, qr_y + qr_size), outline=LINE, width=2, fill=None)
        textRenderer._text_center(invoice, d, qr_x + qr_size / 2, qr_y + qr_size / 2, "QR", textRenderer._f10, (170, 170, 170))
        
        textRenderer._text(invoice, d,(qr_x + qr_size + mm(5), qr_y), "Děkujeme za Váš nákup.", font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice, d,(qr_x + qr_size + mm(5), qr_y + mm(5)), "Faktura byla vygenerována automaticky.", font=textRenderer._f10, fill=INK)
        
        # Souhrny DPH - vpravo dole
        vat_summary_x = _A4_W_PX - margin_r - mm(80)
        y_vat = _A4_H_PX - mm(35)
        textRenderer._text(invoice, d,(vat_summary_x, y_vat), "Souhrn DPH:", font=textRenderer._f11b, fill=INK)
        y_vat += mm(5)
        for v in data.vat:
            x_end, percentage_id = textRenderer._text(invoice, d,(vat_summary_x, y_vat), label="Sazba", text=f"{safe(v.vat_percentage)}", end="%",font=textRenderer._f10, fill=INK, span_tag=SpanTag.O)
            x_end, base_id = textRenderer._text(invoice, d,(x_end, y_vat), label="Základ", text=f"{safe(v.vat_base)}", font=textRenderer._f10, fill=INK, span_tag=SpanTag.O)
            x_end, vat_id = textRenderer._text(invoice, d,(x_end, y_vat), label="DPH", text=f"{safe(v.vat)}",font=textRenderer._f10, fill=INK, span_tag=SpanTag.O)
            y_vat += mm(4)

        hr(_A4_H_PX - mm(15), "strong")
        
        textRenderer._text_center(invoice, d, _A4_W_PX / 2, _A4_H_PX - mm(12), "Strana 1 z 1", textRenderer._f10, INK)
        textRenderer._text(invoice, d,(_A4_W_PX - margin_r, _A4_H_PX - mm(12)), f"Tisk: {datetime.now().strftime('%d.%m.%Y %H:%M')}", font=textRenderer._f10, fill=INK)

        invoice.image = img
        return True
