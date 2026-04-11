from datetime import datetime
from typing import final

from PIL import Image, ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.enumerates.SpanTag import SpanTag

from common.utils.consts import _A4_H_PX, _A4_W_PX, INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG
from common.utils.utilities import mm
from common.utils.utilities import safe, fmt_money


@final
class AlzaInvoice(InvoiceTemplate):


    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # Okraje (podle .page padding)
        margin_l = mm(14)
        margin_r = mm(14)
        margin_t = mm(12)
        margin_b = mm(14)

        # Plátno
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        # Pomocné čáry
        def hr(y:int, weight:str="mid", x0:int|None=None, x1:int|None=None)->None:
            x0 = margin_l if x0 is None else x0
            x1 = _A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        # Start Y
        y = margin_t

        # --- HLAVIČKA ---
        # Logo/jméno dodavatele vlevo
        textRenderer._text(invoice,(margin_l, y), text=safe(data.supplier.name), font=textRenderer._f16b, fill=INK)

        # Titul (centrovaný blok vpravo části)
        title_center_x = _A4_W_PX // 2
        textRenderer._text_center(invoice, title_center_x, y, text=f"{safe(data.invoice_number)}", font=textRenderer._f17b, fill=INK, label="Faktura -", span_tag=SpanTag.INVOICE_NUMBER)
        textRenderer._text_center(invoice, title_center_x, y + mm(12), "záruční a dodací list -", textRenderer._f12, MUTED)

        y += mm(18)
        local_x = margin_l
        # --- Prodávající ---
        textRenderer._text(invoice,(margin_l, y), text=f"Prodávající: {safe(data.supplier.name)} {data.supplier.type.value}", font=textRenderer._f12b,
                fill=INK)
        
        y += mm(5.2)
        local_x, _ = textRenderer._text(invoice,(local_x, y),
                text=f"{safe(data.supplier.address)},",
                font=textRenderer._f11, fill=INK)
        
        local_x, _ = textRenderer._text(invoice,(local_x, y),
                text=f"{safe(data.supplier.register_id)}",
                font=textRenderer._f11, fill=INK, span_tag=SpanTag.SUPPLIER_REGISTER_ID, label="IČ: ", end=",")

        local_x, _ = textRenderer._text(invoice,(local_x, y),
                text=f"{safe(data.supplier.tax_id)}",
                font=textRenderer._f11, fill=INK, span_tag=SpanTag.SUPPLIER_TAX_ID, label="DIČ: ", end=",")
        

        local_x, _ = textRenderer._text(invoice,(local_x, y),
                text=f"internet: www.{safe(data.supplier.name)}.cz, kontakt: www.{safe(data.supplier.name)}.cz/kontakt",
                font=textRenderer._f11, fill=INK)

        y += mm(4)

        y += mm(1.5)

        # --- Dva sloupce ---
        col_gap = mm(24)
        table_w = _A4_W_PX - margin_l - margin_r
        col_w = (table_w - col_gap) // 2
        left_x = margin_l
        right_x = margin_l + col_w + col_gap

        # Levý blok
        textRenderer._text(invoice,(left_x, y), text="Daňový doklad:", font=textRenderer._f12b, fill=INK)
        y_left = y + mm(6)

        kv_label_w = mm(60)

        def kv_row(x:int, y_:int, label:str, value:str, bold:bool=True, tag: SpanTag = SpanTag.O, undersampling:bool = True)->None:
            textRenderer._text(invoice,(x, y_), text=label, font=textRenderer._f11, fill=INK, span_tag=SpanTag.O)
            fontv = textRenderer._f11b if bold else textRenderer._f11
            textRenderer._text(invoice,(x + kv_label_w, y_), text=value, font=fontv, fill=INK, span_tag=tag)

        kv_row(left_x, y_left, "Doklad:", "Faktura");
        y_left += mm(5.2)
        kv_row(left_x, y_left, "Datum vystavení:", value=safe(data.issue_date), tag=SpanTag.ISSUE_DATE);
        y_left += mm(5.2)
        kv_row(left_x, y_left, "Datum uskuteč. zdan. plnění:", value=safe(data.taxable_supply_date), tag=SpanTag.TAXABLE_SUPPLY_DATE);
        y_left += mm(5.2)
        kv_row(left_x, y_left, "Datum splatnosti:", value=safe(data.due_date), tag=SpanTag.DUE_DATE);
        y_left += mm(5.2)
        kv_row(left_x, y_left, "Způsob úhrady:", value=safe(data.payment_type), tag=SpanTag.PAYMENT_TYPE);
        y_left += mm(5.2)

        textRenderer._text(invoice,(left_x, y_left + mm(2)), text="Bankovní účet:", font=textRenderer._f12b, fill=INK)
        y_left += mm(8)
        kv_row(left_x, y_left, label=f"{data.bank_account.name}: ",  value=safe(data.bank_account_number), tag=SpanTag.BANK_ACCOUNT_NUMBER);
        y_left += mm(5.2)
        kv_row(left_x, y_left, f"IBAN:", safe(data.IBAN), tag=SpanTag.IBAN);
        y_left += mm(5.2)
        kv_row(left_x, y_left, f"BIC:", safe(data.bank_account.BIC), tag=SpanTag.BIC);
        y_left += mm(6)
        kv_row(left_x, y_left, "Variabilní symbol:", safe(data.variable_symbol), tag=SpanTag.VARIABLE_SYMBOL);
        y_left += mm(8)

        # Pravý blok
        textRenderer._text(invoice,(right_x, y), text="Kupující:", font=textRenderer._f12b, fill=INK)
        y_right = y + mm(6)
        d.line([(right_x, y_right), (right_x + col_w, y_right)], fill=LINE_MID, width=2)

        # obsah rámečku
        inner_x = right_x + mm(3)
        y_tmp = y_right + mm(3)

        def kv_r(label:str, value:str, tag: SpanTag = SpanTag.O, undersampling:bool = True)->None:
            textRenderer._text(invoice,(inner_x, y_tmp), text=label, font=textRenderer._f11, fill=INK)
            textRenderer._text(invoice,(inner_x + mm(40), y_tmp), text=safe(value), font=textRenderer._f11b, fill=INK, span_tag=tag)

        kv_r("Jméno:", data.customer.name);
        y_tmp += mm(5.2)
        kv_r("Adresa:", data.customer.address);
        y_tmp += mm(5.2)
        kv_r("IČ:", data.customer.register_id, SpanTag.CUSTOMER_REGISTER_ID);
        y_tmp += mm(5.2)
        kv_r("DIČ:", data.customer.tax_id, SpanTag.CUSTOMER_TAX_ID);
        y_tmp += mm(5.2)

        # posun Y pro další bloky
        y = max(y_left, y_tmp) + mm(4)

        # --- TABULKA POLOŽEK ---
        headers = ["Popis", "Ks", "Cena ks", "bez DPH", "DPH %", "DPH", "Cena s DPH"]
        col_ws = [0.36, 0.08, 0.12, 0.12, 0.08, 0.12, 0.12]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin_l]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        # hlavička
        head_h = mm(7)
        d.rectangle((margin_l, y, margin_l + table_w, y + head_h), outline=None)
        baseline = y + mm(2)
        for i, h in enumerate(headers):
            if i == 0:
                textRenderer._text(invoice,(x_cols[i] + 6, baseline), h, font=textRenderer._f11b, fill=INK, must_have_same_width=True)
            elif i in (1, 4):
                textRenderer._text_center(invoice, x_cols[i] + col_abs[i] / 2, baseline, h, textRenderer._f11b, INK, must_have_same_width=True)
            else:
                textRenderer._text_right(invoice, x_cols[i] + col_abs[i] - 6, baseline, h, textRenderer._f11b, INK, must_have_same_width=True)
        y += head_h
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)

        # tělo
        row_h = mm(6.5)
        for it in data.items:
            y += row_h
            # oddělovací linka
            d.line((margin_l, y, margin_l + table_w, y), fill=LINE, width=2)

            cells = [
                safe(it.description),
                safe(it.quantity),
                fmt_money(it.ppu),
                fmt_money(it.price_without_vat),
                f"{safe(it.vat_percentage)}%",
                fmt_money(it.vat),
                fmt_money(it.price_with_vat),
            ]
            # vykreslení buněk
            y_text = y - row_h + mm(2)
            # 0 - popis (vlevo)
            textRenderer._text(invoice,(x_cols[0] + 6, y_text), cells[0], font=textRenderer._f11, fill=INK)
            # 1 - ks (střed)
            textRenderer._text_center(invoice, x_cols[1] + col_abs[1] / 2, y_text, cells[1], textRenderer._f11, INK)
            # 2..6 - doprava
            textRenderer._text_right(invoice, x_cols[2] + col_abs[2] - 6, y_text, cells[2], textRenderer._f11, INK)
            textRenderer._text_right(invoice, x_cols[3] + col_abs[3] - 6, y_text, cells[3], textRenderer._f11, INK)
            textRenderer._text_center(invoice, x_cols[4] + col_abs[4] / 2, y_text, cells[4], textRenderer._f11,INK)
            textRenderer._text_right(invoice, x_cols[5] + col_abs[5] - 6, y_text, cells[5], textRenderer._f11, INK)
            textRenderer._text_right(invoice, x_cols[6] + col_abs[6] - 6, y_text, cells[6], textRenderer._f11, INK)

        # tfoot
        y += mm(1.8)
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)
        y += mm(1)
        foot_h = mm(8)

        textRenderer._text(invoice,(margin_l + 6, y + mm(2.5)), "Celkem:", font=textRenderer._f11b, fill=INK)
        total_txt = f"{fmt_money(data.calculated_total_price)}"
        textRenderer._text_right(invoice, margin_l + table_w - 6, y + mm(2.5), total_txt, textRenderer._f11b, INK,end=f"{data.currency.value if hasattr(data.currency, 'value') else data.currency}", span_tag=SpanTag.TOTAL)
        y += foot_h

        # hr(y, "mid")
        y += mm(2)

        # --- SOUHRNY (DPH vlevo) ---
        box_x = margin_l
        right_summary_w = mm(64)
        gap = mm(10)
        box_w = table_w - right_summary_w - gap
        rows = max(1, len(data.vat))
        box_h = mm(12) + rows * mm(7) + mm(8)

        textRenderer._text(invoice,(box_x + mm(6), y + mm(3)), "Vyčíslení DPH:", font=textRenderer._f12b, fill=INK)
        head_y = y + mm(9)
        textRenderer._text_center(invoice, box_x + box_w * 0.16, head_y, "Sazba", textRenderer._f11b, INK)
        textRenderer._text_center(invoice, box_x + box_w * 0.50, head_y, "Základ", textRenderer._f11b,INK)
        textRenderer._text_center(invoice, box_x + box_w * 0.84, head_y, "DPH", textRenderer._f11b, INK)
        d.line((box_x + 4, head_y + mm(4), box_x + box_w - 4, head_y + mm(4)), fill=LINE_STRONG,
                width=3)

        row_y = head_y + mm(6.5)
        for v in data.vat:
            _, percentage_id = textRenderer._text_center(invoice, box_x + box_w * 0.16, row_y, text=f"{safe(v.vat_percentage)}", end=" %", font=textRenderer._f11, fill=INK, span_tag=SpanTag.O)
            _, base_id = textRenderer._text_right(invoice, box_x + box_w * 0.66, row_y, fmt_money(v.vat_base), textRenderer._f11, INK, span_tag=SpanTag.O)
            _, vat_id = textRenderer._text_right(invoice, box_x + box_w - mm(6), row_y, fmt_money(v.vat), textRenderer._f11, INK, span_tag=SpanTag.O)
            d.line((box_x + 4, row_y + mm(3.5), box_x + box_w - 4, row_y + mm(3.5)), fill=LINE, width=1)
            
            row_y += mm(7)

        # Pravý souhrn
        right_block_x = margin_l + box_w + gap
        textRenderer._text(invoice,(right_block_x + mm(25), y + mm(2)),
                f"Zaokrouhlení: 0,00 {data.currency.value if hasattr(data.currency, 'value') else data.currency}",
                font=textRenderer._f11, fill=INK)
        textRenderer._text(invoice,(right_block_x + mm(25), y + mm(2) + mm(6)),
                text=f"{fmt_money(data.calculated_total_price)}",
                label="CELKEM: ", end=f" {data.currency.value if hasattr(data.currency, 'value') else data.currency}",font=textRenderer._f13b, fill=INK, span_tag=SpanTag.TOTAL)

        y = max(y + box_h, y + mm(2) + mm(12))

        hr(y, "thin")
        y += mm(4)

        # --- PATIČKA ---
        textRenderer._text(invoice,(margin_l, y), "Poznámka:", font=textRenderer._f11, fill=INK)
        y += mm(10)

        # QR box vpravo
        qr_size = mm(22)
        qr_x = _A4_W_PX - margin_r - qr_size
        qr_y = y
        d.rectangle((qr_x, qr_y, qr_x + qr_size, qr_y + qr_size), outline=LINE, width=2, fill=None)
        textRenderer._text_center(invoice, qr_x + qr_size / 2, qr_y + qr_size / 2 - mm(2), "QR", textRenderer._f10, (170, 170, 170))

        # Spodní lišta
        bar_y = qr_y + mm(22) + mm(8)
        hr(bar_y, "thin")
        textRenderer._text(invoice,(margin_l, bar_y + mm(2)), "Ochranný znak …", font=textRenderer._f11, fill=INK)
        textRenderer._text_center(invoice, _A4_W_PX / 2, bar_y + mm(2), "Strana 1 z 1", textRenderer._f11, INK)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, bar_y + mm(2), f"Tisk: {now_str}", textRenderer._f11, INK)

   
        invoice.image = img
        return True

