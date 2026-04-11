from datetime import datetime
from typing import final

from PIL import Image, ImageDraw, ImageFont


from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.enumerates.SpanTag import SpanTag
from common.utils.consts import _A4_W_PX, _A4_H_PX, INK, LINE, LINE_MID, LINE_STRONG, BG
from common.utils.utilities import mm
from common.utils.utilities import safe, fmt_money



@final
class AInvoice(InvoiceTemplate):

    

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        
        # Okraje (zjednodušené pro nový vzhled)
        margin_l = mm(20)
        margin_r = mm(20)
        margin_t = mm(15)
        
        # Plátno
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        # Pomocné čáry (funkce hr)
        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = _A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        # Start Y
        y = margin_t

        # --- HLAVIČKA ---
        # Titul a číslo faktury (vpravo nahoře)
        title_x = _A4_W_PX - margin_r - mm(80)
        textRenderer._text(invoice,(title_x, y), "Faktura - Daňový doklad", font=textRenderer._f17b, fill=INK)
        y += mm(8)
        textRenderer._text(invoice,(title_x, y), f"{safe(data.invoice_number)}", label="Číslo dokladu: ", font=textRenderer._f13b, fill=INK, span_tag=SpanTag.INVOICE_NUMBER)
        y += mm(10)
        
        # Logo/Jméno vlevo nahoře (pokud není logo, použije se jméno)
        textRenderer._text(invoice,(margin_l, margin_t), safe(data.supplier.name).upper(), font=textRenderer._f16b, fill=INK)

        y_sep = max(y, margin_t + mm(18)) + mm(5)

        # --- KUPUJÍCÍ A PRODÁVAJÍCÍ VEDLE SEBE ---
        col_sep = mm(10)
        col_w = (_A4_W_PX - 2 * margin_l - col_sep) // 2
        
        # Prodávající (Levý sloupec)
        y_left = y_sep
        textRenderer._text(invoice,(margin_l, y_left), "Dodavatel (Prodávající):", font=textRenderer._f12b, fill=INK)
        y_left += mm(6)
        
        textRenderer._text(invoice,(margin_l, y_left), safe(data.supplier.name), font=textRenderer._f11b, fill=INK)
        y_left += mm(4)
        textRenderer._text(invoice,(margin_l, y_left), safe(data.supplier.address), font=textRenderer._f11, fill=INK)
        y_left += mm(4)
        textRenderer._text(invoice,(margin_l, y_left), label="IČ: ",text=f"{safe(data.supplier.register_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        y_left += mm(4)
        textRenderer._text(invoice,(margin_l, y_left), label="DIČ: ",text=f"{safe(data.supplier.tax_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.SUPPLIER_TAX_ID)
        y_left += mm(4)

        # Kupující (Pravý sloupec)
        right_x = margin_l + col_w + col_sep
        y_right = y_sep
        textRenderer._text(invoice,(right_x, y_right), "Odběratel (Kupující):", font=textRenderer._f12b, fill=INK)
        y_right += mm(6)
        
        textRenderer._text(invoice,(right_x, y_right), safe(data.customer.name), font=textRenderer._f11b, fill=INK)
        y_right += mm(4)
        textRenderer._text(invoice,(right_x, y_right), safe(data.customer.address), font=textRenderer._f11, fill=INK)
        y_right += mm(4)
        textRenderer._text(invoice,(right_x, y_right), label="IČ: ", text=f"{safe(data.customer.register_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.CUSTOMER_REGISTER_ID)
        y_right += mm(4)
        textRenderer._text(invoice,(right_x, y_right), label="DIČ: ",text=f"{safe(data.customer.tax_id)}", font=textRenderer._f11, fill=INK, span_tag=SpanTag.CUSTOMER_TAX_ID)
        y_right += mm(4)

        # Nová startovací pozice Y
        y = max(y_left, y_right) + mm(5)

        hr(y, "mid")
        y += mm(3)

        # --- DATUMY A PLATBA (Pod sebou) ---
        kv_x = margin_l
        kv_y = y
        kv_label_w = mm(40) # užší sloupec pro popisky

        def kv_row(x:int, y_:int, label:str, value:str, before_value:str|None = None, bold:bool=True, tag: SpanTag = SpanTag.O, undersampling:bool = True)->None:
            x_label_end, _ = textRenderer._text(invoice,(x, y_), label, font=textRenderer._f11, fill=INK, span_tag=SpanTag.O)
            fontv = textRenderer._f11b if bold else textRenderer._f11

            textRenderer._text(invoice,(x_label_end, y_), value, font=fontv, fill=INK, span_tag=tag)

        kv_row(kv_x,kv_y, "Datum vystavení:", safe(data.issue_date), tag = SpanTag.ISSUE_DATE)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "Datum splatnosti:", safe(data.due_date), tag = SpanTag.DUE_DATE)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "Způsob úhrady:", safe(data.payment_type), tag=SpanTag.PAYMENT_TYPE)
        kv_y += mm(8)
        kv_row(kv_x,kv_y, f"Bankovní spojení: {data.bank_account.name} ", value=f"{safe(data.bank_account_number)}", tag=SpanTag.BANK_ACCOUNT_NUMBER);
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "IBAN:", safe(data.IBAN), tag=SpanTag.IBAN)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "Variabilní symbol:", safe(data.variable_symbol), tag=SpanTag.VARIABLE_SYMBOL)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "Konstantní symbol:", safe(data.const_symbol), tag=SpanTag.CONST_SYMBOL)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "BIC:", safe(data.bank_account.BIC), tag=SpanTag.BIC)
        kv_y += mm(5)

        y = kv_y + mm(5)
        hr(y, "mid")
        y +=mm(5)

        # --- TABULKA POLOŽEK (Jednodušší) ---
        table_w = _A4_W_PX - 2 * margin_l
        
        # Nové sloupce (Popis, Ks, Cena/ks s DPH, Celkem s DPH) - méně detailní
        headers = ["Popis zboží/služby", "Ks", "Jednotková cena bez DPH", "Celková cena s DPH"]
        # Nastavení šířek: 50% pro Popis, 10% pro Ks, 20% pro Jednotková cena, 20% pro Celkem
        col_ws = [0.30, 0.10, 0.30, 0.30]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin_l]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        # hlavička tabulky
        head_h = mm(7)
        baseline = y +mm(2)
        
        for i, h in enumerate(headers):
            if i == 0:
                textRenderer._text(invoice,(x_cols[i] + 6, baseline), h, font=textRenderer._f11b, fill=INK, must_have_same_width=True)
            elif i == 1:
                # Ks - vystředěno
                textRenderer._text_center(invoice, x_cols[i] + col_abs[i] / 2, baseline, h, textRenderer._f11b, INK, must_have_same_width=True)
            else:
                # Ostatní - doprava
                textRenderer._text_right(invoice, x_cols[i] + col_abs[i] - 6, baseline, h, textRenderer._f11b,INK, must_have_same_width=True)
        
        y += head_h
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)

        # tělo tabulky
        row_h = mm(7)
        for it in data.items:
            y += row_h
            # oddělovací linka
            d.line((margin_l, y, margin_l + table_w, y), fill=LINE, width=1)

            cells = [
                safe(it.description),
                safe(it.quantity),
                fmt_money(it.ppu), # Nová hodnota
                fmt_money(it.price_with_vat), # Nová hodnota
            ]
            
            # vykreslení buněk
            y_text = y - row_h + mm(2)
            
            # 0 - popis (vlevo)
            textRenderer._text(invoice,(x_cols[0] + 6, y_text), cells[0], font=textRenderer._f11, fill=INK)
            # 1 - ks (střed)
            textRenderer._text_center(invoice, x_cols[1] + col_abs[1] / 2, y_text, cells[1], textRenderer._f11, INK)
            # 2..3 - doprava
            textRenderer._text_right(invoice, x_cols[2] + col_abs[2] - 6, y_text, cells[2], textRenderer._f11, INK)
            textRenderer._text_right(invoice, x_cols[3] + col_abs[3] - 6, y_text, cells[3], textRenderer._f11, INK)

        # Zvýraznění celkové ceny na konci tabulky
        y += mm(1.8)
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)
        y += mm(1)
        foot_h = mm(8)

        # Celková cena
        textRenderer._text(invoice,(margin_l + 6, y + mm(2.5)), "CELKEM K ÚHRADĚ:", font=textRenderer._f12b, fill=INK)
        textRenderer._text_right(invoice, margin_l + table_w - 6, y + mm(2.5), text=f"{fmt_money(data.calculated_total_price)}", end=f" {data.currency.value if hasattr(data.currency, 'value') else data.currency}", font=textRenderer._f13b, fill=INK, span_tag=SpanTag.TOTAL)
        y += foot_h

        hr(y, "strong") # Silná čára oddělující tabulku od souhrnu
        y += mm(5)

        # --- SOUHRNY DPH A POZNÁMKA ---
        
        # Souhrn DPH (Vlevo)
        vat_summary_x = margin_l
        vat_summary_w = mm(80)
        textRenderer._text(invoice,(vat_summary_x, y), "Přehled DPH:", font=textRenderer._f12b, fill=INK)
        y_vat = y + mm(6)
        
        for v in data.vat:
            x_vat, percentage_id = textRenderer._text(invoice, (vat_summary_x, y_vat), label="Sazba " ,text=f"{safe(v.vat_percentage)}", end=" %:", span_tag=SpanTag.O, font=textRenderer._f11,
                                    fill=INK)
            
            x_vat, base_id = textRenderer._text(invoice, (vat_summary_x+x_vat, y_vat), label="Základ " ,text=f"{fmt_money(v.vat_base)}", end=" Kč", span_tag=SpanTag.O, font=textRenderer._f11
                                , fill=INK)

            x_vat, vat_id =textRenderer._text(invoice, (vat_summary_x+x_vat, y_vat), label="DPH ", text=f"{fmt_money(v.vat)}",span_tag=SpanTag.O, fill=INK, font=textRenderer._f11)

            y_vat += mm(4)
        
        # Poznámka (Vpravo)
        note_x = margin_l
        y_vat += mm(5)
        textRenderer._text(invoice,(note_x, y_vat), "Poznámka:", font=textRenderer._f12b, fill=INK)
        textRenderer._text(invoice,(note_x, y_vat + mm(6)), "Děkujeme za Váš nákup!", font=textRenderer._f11, fill=INK)
        
        y = y_vat + mm(10)
        
        # --- PATIČKA ---
        bar_y = _A4_H_PX - mm(12)
        hr(bar_y, "thin")
        textRenderer._text(invoice,(margin_l, bar_y + mm(2)), "Generováno pro účely testování OCR.", font=textRenderer._f10, fill=INK)
        textRenderer._text_center(invoice, _A4_W_PX / 2, bar_y + mm(2), "Strana 1 z 1", textRenderer._f10, INK)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, bar_y + mm(2), f"Tisk: {now_str}", textRenderer._f10, INK)

        # Uložení
        invoice.image = img
        return True
