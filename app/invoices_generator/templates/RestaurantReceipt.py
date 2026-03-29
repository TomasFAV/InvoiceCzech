from typing import final
from PIL import Image, ImageDraw, ImageFont

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.enumerates.SpanTag import SpanTag

from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX, INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG
from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money



@final
class RestaurantReceipt(InvoiceTemplate):
    """
    Vykreslí účtenku jako „papírový“ lístek
    """


    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # A4 plátno – účtenku vykreslíme jako úzký pás uprostřed
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        # Rozměr účtenky (lístku)
        ticket_w = mm(95)         # ~95 mm šířka pásky
        ticket_x = (_A4_W_PX - ticket_w) // 2
        margin_t = mm(15)
        y = margin_t
        x0 = ticket_x
        x1 = ticket_x + ticket_w

        # Pomocné čáry
        def hr(ypos:int, weight:str="thin") -> None:
            color = LINE if weight == "thin" \
                else (LINE_MID if weight == "mid" else LINE_STRONG)
            width = 2 if weight in ("thin","mid") else 3
            d.line([(x0, ypos), (x1, ypos)], fill=color, width=width)

        # Horní okraj
        d.rectangle((x0, y, x1, y + mm(1)), fill=BG)
        y += mm(3)

        # --- HLAVIČKA (dynamicky ze supplier) ---
        supplier_name = safe(getattr(data.supplier, "name", ""))
        supplier_addr = safe(getattr(data.supplier, "address", ""))

        textRenderer._text_center(invoice, d, (x0 + x1)//2, y, supplier_name or "—", textRenderer._f14b, INK)
        y += mm(6)
        # Druhý řádek (volitelný, např. „PIZZERIE…“ – použijeme supplier_name znovu, ať je to obecné)
        textRenderer._text_center(invoice, d, (x0 + x1)//2, y, supplier_name, textRenderer._f10, MUTED)
        y += mm(5)
        if supplier_addr:
            textRenderer._text_center(invoice, d, (x0 + x1)//2, y, supplier_addr, textRenderer._f10, MUTED)
            y += mm(3)
        else:
            y += mm(3)
        #IČ, DIČ
        x_now, _ = textRenderer._text(invoice, d, ((x0 + x1)//2 - mm(15), y), label="IČ: ", text=f"{data.supplier.register_id}", end=",", font=textRenderer._f10, fill=MUTED, span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        textRenderer._text(invoice, d, (x_now, y), label="DIČ: ", text=f"{data.supplier.tax_id}", font=textRenderer._f10, fill=MUTED, span_tag=SpanTag.SUPPLIER_TAX_ID)
        y += mm(5)
        hr(y, "thin")
        y += mm(3)

        # --- META ÚDAJE ---
        kv_label_x = x0 + mm(3)
        kv_val_x = x1 - mm(3)

        def kv(label:str, value:str, bold:bool=False, tag:SpanTag = SpanTag.O, undersampling:bool = True) -> None:
            nonlocal y
            textRenderer._text(invoice, d,(kv_label_x, y), label, font=textRenderer._f11, fill=INK)
            textRenderer._text_right(invoice, d, kv_val_x, y, safe(value), textRenderer._f11b if bold else textRenderer._f11, INK, span_tag=tag)
            y += mm(5)

        # mapování na invoice
        kv("Účtenka:", str(data.invoice_number), bold=True, tag=SpanTag.INVOICE_NUMBER)
        kv("Objednávka:", str(data.variable_symbol), bold=True, tag=SpanTag.VARIABLE_SYMBOL)  # není-li objednávka, použijeme VS
        kv("Datum:", data.issue_date, tag=SpanTag.ISSUE_DATE)
        pay_str = data.payment_type
        kv("Způsob úhrady:", pay_str, tag=SpanTag.PAYMENT_TYPE)
        y += mm(2)
        hr(y, "thin")
        y += mm(3)

        # --- TABULKA POLOŽEK ---
        col_name_w = int(ticket_w * 0.35)
        col_qty_w  = int(ticket_w * 0.19)
        col_price_w= int(ticket_w * 0.25)
        col_total_w= ticket_w - col_name_w - col_qty_w - col_price_w

        col_x = [
            x0,
            x0 + col_name_w,
            x0 + col_name_w + col_qty_w,
            x0 + col_name_w + col_qty_w + col_price_w,
            x1
        ]

        def th(txt:str, col:int, font:ImageFont.FreeTypeFont) -> None:
            cx = (col_x[col] + col_x[col+1])//2
            textRenderer._text_center(invoice, d, cx, y, txt, font, INK)

        th("Název", 0, textRenderer._f11b); th("Počet", 1, textRenderer._f11b); th("Cena", 2, textRenderer._f11b); th("Celkem", 3, textRenderer._f11b)
        y += mm(6)
        hr(y, "mid")

        def row(name:str, qty:str, price:str, total:str) -> None:
            nonlocal y
            y += mm(2.5)
            textRenderer._text(invoice, d,(col_x[0] + mm(2), y), safe(name), font=textRenderer._f10, fill=INK)
            x_end, _ = textRenderer._text_center(invoice, d, (col_x[1] + col_x[2])//2, y, safe(qty), textRenderer._f10, INK)
            textRenderer._text(invoice, d, (col_x[2], y), safe(price), textRenderer._f10, INK)
            textRenderer._text_right(invoice, d, col_x[4] - mm(2), y, safe(total), textRenderer._f10, INK)
            y += mm(6)
            d.line([(x0, y), (x1, y)], fill=LINE, width=1)

        # řádky z data.items
        curr = data.currency.value if hasattr(data.currency, "value") else str(data.currency)
        for it in data.items:
            qty = getattr(it, "quantity", None)
            unit = getattr(it, "unit", "ks")
            qty_txt = f"{qty} {unit}" if qty is not None else ""
            if getattr(it, "ppu") is not None:
                ppu_val = it.ppu
            price_txt = f"{fmt_money(ppu_val)} {curr}" if ppu_val is not None else ""
            total_txt = f"{fmt_money(getattr(it, 'price_with_vat', 0))} {curr}"
            row(getattr(it, "description", ""), qty_txt, price_txt, total_txt)

        y += mm(3)

        # --- SOUHRN / TOTALY ---
        kv_label_x = x0 + mm(3)
        kv_val_x = x1 - mm(3)

        def total_line(label:str, value:str, end:str|None = None, big:bool=False, label_tag:SpanTag=SpanTag.O,tag:SpanTag = SpanTag.O) -> None:
            nonlocal y
            textRenderer._text(invoice, d,(kv_label_x, y), label, font=textRenderer._f11b if big else textRenderer._f11, fill=INK, span_tag=label_tag)
            x_n, _ = textRenderer._text_right(invoice, d, kv_val_x, y, value, textRenderer._f12b if big else textRenderer._f11, INK, span_tag=tag)
            textRenderer._text(invoice, d, (x_n, y), end, textRenderer._f12b if big else textRenderer._f11, INK)
            y += mm(6 if big else 5)

        def total_line_summary(label0:str,label1:str, value0:str, value1:str,end0:str|None = None, end1:str|None = None, big0:bool=False, big1:bool=False,
                                label_tag0:SpanTag=SpanTag.O, label_tag1:SpanTag=SpanTag.O, tag0:SpanTag = SpanTag.O, tag1:SpanTag = SpanTag.O ) -> None:
            nonlocal y
            textRenderer._text(invoice, d,(kv_label_x, y), label0, font=textRenderer._f11b if big0 else textRenderer._f11, fill=INK, span_tag=label_tag0)
            x_n, base_id = textRenderer._text_right(invoice, d, kv_val_x, y, value0, textRenderer._f12b if big0 else textRenderer._f11, INK, span_tag=tag0)
            textRenderer._text(invoice, d, (x_n, y), end0, textRenderer._f12b if big0 else textRenderer._f11, INK)
            y += mm(6 if big0 else 5)
            y += mm(2)

            _, percentage_id = textRenderer._text(invoice, d,(kv_label_x, y), label1, font=textRenderer._f11b if big1 else textRenderer._f11, fill=INK, span_tag=label_tag1)
            x_n, vat_id = textRenderer._text_right(invoice, d, kv_val_x, y, value1, textRenderer._f12b if big1 else textRenderer._f11, INK, span_tag=tag1)
            textRenderer._text(invoice, d, (x_n, y), end1, textRenderer._f12b if big1 else textRenderer._f11, INK)
            
            y += mm(6 if big0 else 5)
            y += mm(2)
            
            y += mm(2)

            return y



        # DPH po sazbách (dynamicky z data.vat)
        for v in data.vat:
            y = total_line_summary(label0=f"Základ ({safe(v.vat_percentage)}%)", value0=f"{fmt_money(v.vat_base)} ", end0=f"{curr}",label_tag0=SpanTag.O, tag0=SpanTag.O,
                        label1=f"DPH ({safe(v.vat_percentage)}%)", value1=f"{fmt_money(v.vat)} ", end1=f"{curr}", label_tag1=SpanTag.O, tag1=SpanTag.O)
            hr(y, "thin")

            y += mm(2)


        # CELKEM
        hr(y, "mid"); y += mm(2.5)
        total_line(label="Celkem", value=f"{fmt_money(data.calculated_total_price)}", end=f"{curr}", big=True, tag=SpanTag.TOTAL)

        y += mm(3)
        hr(y, "thin")
        y += mm(3)

        # --- ZÁKAZNÍK ---
        customer_name = safe(getattr(data.customer, "name", ""))
        if customer_name:
            textRenderer._text(invoice, d,(kv_label_x, y), "Zákazník:", font=textRenderer._f11, fill=INK)
            textRenderer._text_right(invoice, d, kv_val_x, y, customer_name, textRenderer._f11b, INK)
            y += mm(6)

        # --- PATIČKA / POZNÁMKY ---
        y += mm(2)
        # „badge“ se způsobem úhrady
        badge_txt = f"Způsob úhrady: {pay_str}"
        w_badge = d.textlength(badge_txt, font=textRenderer._f10) + mm(6)
        bx0 = max(x0 + mm(2), (x0 + x1 - w_badge)//2)
        by0 = y
        by1 = by0 + mm(7)
        x_end, _ = textRenderer._text_center(invoice, d, (x0 + x1)//2, by0 + mm(1.5), label="Způsob úhrady:", text=f"{pay_str}", font=textRenderer._f10, fill=INK, span_tag=SpanTag.PAYMENT_TYPE)
        d.rectangle((bx0, by0, x_end, by1), outline=LINE, width=2, fill=None)
        y = by1 + mm(4)




        invoice.image = img
        return True
