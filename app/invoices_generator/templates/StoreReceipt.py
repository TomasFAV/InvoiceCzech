from typing import final

from PIL import Image, ImageDraw
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.invoice.renderers.TextRenderer import TextRenderer
from common.enumerates.SpanTag import SpanTag

from common.utils.consts import _A4_H_PX, _A4_W_PX, INK, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, BOX_BG
from common.utils.utilities import mm
from common.utils.utilities import safe, fmt_money


@final
class StoreReceipt(InvoiceTemplate):
    """
    Dynamická účtenka ve stylu 'DAŇOVÝ DOKLAD'
    """        

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        # „termopáska“ uprostřed A4
        ticket_w = mm(95)  # ~95 mm šířky
        x0 = (_A4_W_PX - ticket_w) // 2
        x1 = x0 + ticket_w
        y = mm(12)

        def hr(ypos:int, weight:str="thin")->None:
            color = LINE if weight=="thin" else (LINE_MID if weight=="mid" else LINE_STRONG)
            width = 2 if weight!="strong" else 3
            d.line([(x0, ypos), (x1, ypos)], fill=color, width=width)


        def kv_row(lbl:str, val:str, tag:SpanTag = SpanTag.O, undersampling:bool = True)->None:
            nonlocal y
            textRenderer._text(invoice,(x0+mm(3), y), lbl, font=textRenderer._f11, fill=INK)
            textRenderer._text_right(invoice, x1-mm(3), y, safe(val), textRenderer._f11b, INK, span_tag=tag)
            y += mm(5)

        # ---------------- HLAVIČKA ----------------
        box_top = y
        d.rectangle((x0, y, x1, y+mm(10)), outline=LINE_STRONG, width=2, fill=SUBTLE_BG)
        textRenderer._text_center(invoice,(x0+x1)//2,y+mm(2), "DAŇOVÝ  DOKLAD", textRenderer._f12b)
        y += mm(14)

        supplier_name = safe(getattr(data.supplier, "name", ""))
        supplier_addr = safe(getattr(data.supplier, "address", ""))
        supplier_dic  = safe(getattr(data.supplier, "tax_id", ""))
        supplier_ico  = safe(getattr(data.supplier, "register_id", ""))

        if supplier_name:
            textRenderer._text_center(invoice,(x0+x1)//2,y, supplier_name, textRenderer._f11b); y += mm(5)
        if supplier_addr:
            textRenderer._text_center(invoice,(x0+x1)//2,y, supplier_addr, textRenderer._f11); y += mm(5)
        if supplier_dic or supplier_ico:
            if supplier_dic:
                textRenderer._text_center(invoice,(x0+x1)//2,y, label="DIČ: ", text=f"{supplier_dic}", font=textRenderer._f11, span_tag=SpanTag.SUPPLIER_TAX_ID); y += mm(4.2)
            if supplier_ico:
                textRenderer._text_center(invoice,(x0+x1)//2,y, label="IČO: ", text=f"{supplier_ico}", font=textRenderer._f11, span_tag=SpanTag.SUPPLIER_REGISTER_ID); y += mm(5)

        hr(y, "thin"); y += mm(2)

        # ---------------- TABULKA HLAVIČKA ----------------
        # sloupce: počet | jedn.cena | sazba DP | cena
        pad = mm(3)
        col_w = [
            int(ticket_w*0.05),  # počet
            int(ticket_w*0.35),  # jedn.cena
            int(ticket_w*0.25),  # sazba
            ticket_w - int(ticket_w*0.25) - int(ticket_w*0.28) - int(ticket_w*0.20)  # cena
        ]
        col_x = [x0+pad, x0+pad+col_w[0], x0+pad+col_w[0]+col_w[1], x0+pad+col_w[0]+col_w[1]+col_w[2], x1-pad]

        def th(i:int, txt:str)->None:
            cx = (col_x[i] + col_x[i+1])//2
            textRenderer._text_center(invoice, cx, y, txt, textRenderer._f11b, INK)

        th(0, "počet")
        th(1, "jedn.cena")
        th(2, "sazba DPH")
        th(3, "cena")
        y += mm(5.5)
        d.line([(x0+pad, y), (x1-pad, y)], fill=LINE_MID, width=2)
        y += mm(1.5)

        # ---------------- POLOŽKY ----------------
        # řádek položky v monospace
        def item_row(qty_txt:str, ppu_txt:str, vat_txt:str, price_txt:str)->None:
            nonlocal y
            # počet (vlevo), jednotková, sazba (střed), cena (vpravo)
            textRenderer._text_right(invoice, col_x[1]-mm(1), y, qty_txt, textRenderer._f11, INK)
            textRenderer._text_right(invoice, col_x[2]-mm(1), y, ppu_txt, textRenderer._f11, INK)
            textRenderer._text_center(invoice, (col_x[2]+col_x[3])//2, y, vat_txt, textRenderer._f11, INK)
            textRenderer._text_right(invoice, col_x[4], y, price_txt, textRenderer._f11, INK)
            y += mm(5.3)

        currency = data.currency.value if hasattr(data.currency, "value") else str(data.currency)

        for it in data.items:
            qty = it.quantity
            unit = getattr(it, "unit", "ks")
            ppu = it.ppu
            if ppu is None:
                try:
                    if qty not in (None, 0):
                        ppu = float(getattr(it, "price_with_vat", 0)) / float(qty)
                except Exception:
                    ppu = getattr(it, "price_with_vat", 0)

            # název (samostatný řádek)
            textRenderer._text(invoice,(x0+pad, y), safe(getattr(it, "description", "")), font=textRenderer._f11, fill=INK)
            y += mm(5)

            qty_txt = f"{safe(qty)} {unit}".strip()
            ppu_txt = f"{fmt_money(ppu)} {currency}" if ppu is not None else ""
            vat_txt = f"{safe(getattr(it, 'vat_percentage', ''))}%"
            price_txt = f"{fmt_money(getattr(it, 'price_with_vat', 0))} {currency}"
            item_row(qty_txt, ppu_txt, vat_txt, price_txt)

        hr(y, "thin"); y += mm(2)

        # ---------------- SOUHRN DPH ----------------
        # sazba   bez DPH   DPH   s DPH
        def sum_header()->None:
            nonlocal y
            textRenderer._text_center(invoice, x0+pad + col_w[0]*0.35, y, "sazba", textRenderer._f11b, INK, must_have_same_width=True)
            textRenderer._text_center(invoice, x0+pad + col_w[0] + col_w[1]*0.55, y, "bez DPH", textRenderer._f11b, INK, must_have_same_width=True)
            textRenderer._text_center(invoice, x0+pad + col_w[0] + col_w[1] + col_w[2]*0.55, y, "DPH", textRenderer._f11b, INK, must_have_same_width=True)
            textRenderer._text_center(invoice, x1-pad - col_w[3]*0.35, y, "s DPH", textRenderer._f11b, INK, must_have_same_width=True)
            y += mm(5)

        sum_header()
        for v in data.vat:
            # řádky souhrnu
            _, percentage_id = textRenderer._text_center(invoice, x0+pad + col_w[0]*0.35, y, text=f"{safe(v.vat_percentage)}", end="%", font= textRenderer._f11,fill=INK, span_tag=SpanTag.O)
            _, base_id = textRenderer._text_right(invoice, x0+pad + col_w[0] + col_w[1] - mm(2), y, text=f"{fmt_money(v.vat_base)}", end=f"{currency}", font= textRenderer._f11, fill=INK, span_tag=SpanTag.O)
            _, vat_id = textRenderer._text_right(invoice, x0+pad + col_w[0] + col_w[1] + col_w[2] - mm(2), y, f"{fmt_money(v.vat)}", end=f"{currency}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.O)
            textRenderer._text_right(invoice, x1-pad, y, f"{fmt_money(float(v.vat_base) + float(v.vat))} {currency}", textRenderer._f11, INK)
            y += mm(5)

        # CELKEM
        y += mm(1)
        d.rectangle((x0, y, x1, y+mm(9)), outline=LINE_STRONG, width=2, fill=BOX_BG)
        textRenderer._text_center(invoice, (x0+x1)//2, y+mm(2), "CELKEM", textRenderer._f11b, INK)
        textRenderer._text_right(invoice, x1-mm(4), y+mm(2), text=f"{fmt_money(data.calculated_total_price)}", end=f"{currency}", font=textRenderer._f11b, fill=INK, span_tag=SpanTag.TOTAL)
        y += mm(12)

        # ---------------- PATIČKA / META ----------------
        hr(y, "thin"); y += mm(3)

        
        kv_row("Účtenka:", str(data.invoice_number), tag=SpanTag.INVOICE_NUMBER)
        kv_row("Vystaveno:", data.issue_date, tag=SpanTag.ISSUE_DATE)

        # Volitelné: číslo pokladny / pokladník – pokud je v description/customer apod.
        cashier = safe(getattr(data.customer, "name", ""))  # když eviduješ pokladníka jako "customer.name"
        if cashier:
            kv_row("Pokladník:", cashier)


        y += mm(2)
        textRenderer._text_center(invoice,(x0+x1)//2,y, "----  DĚKUJEME  ----", textRenderer._f11b)
        y += mm(6)


        invoice.image = img
        return True
