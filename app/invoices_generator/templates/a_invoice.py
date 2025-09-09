from datetime import datetime
import json
import random
from typing import Any, Dict, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

import pytesseract

from app.invoices_generator.core.enumerates.banks import banks
from app.invoices_generator.core.enumerates.span_tags import span_tags
from app.invoices_generator.core.invoice import invoice
from app.invoices_generator.utility.json_encoder import json_encoder
from app.invoices_generator.utility.invoice_consts import fonts


@final
class a_invoice(invoice):

    def to_json_donut(self) -> Any:
        # Používá stejnou logiku pro serializaci jako původní faktura,
        # zajišťující konzistentní výstup dat.
        data = dict(supplier_name = self.supplier.name, customer_name = self.customer.name,
                    issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date="",
                    payment=self.payment.value, BIC=self.bank_account.BIC, bank_account_number=self.bank_account_number, IBAN=self.IBAN,
                    variable_symbol=self.variable_symbol, const_symbol=self.const_symbol,
                    supplier_register_id=self.supplier.register_id, supplier_tax_id=self.supplier.tax_id,
                    customer_register_id=self.customer.register_id, customer_tax_id=self.customer.tax_id,
                    vat_items=self.vat,
                    total_price=self.calculated_total_price, total_vat=None, currency=self.currency,
                    invoice_number=self.invoice_number)

        # zrušení vazeb na instance bank, zákazníků, dodavatelů
        # Používám zjednodušenou serializaci, která by měla fungovat,
        # pokud je json_encoder definován pro vaše vlastní objekty.
        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False, sort_keys=True))

        return j_data


    def generate_img(self, output_path: str) -> bool:
        # Okraje (zjednodušené pro nový vzhled)
        margin_l = self.mm(20)
        margin_r = self.mm(20)
        margin_t = self.mm(15)
        
        # Plátno
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        # Pomocné čáry (funkce hr)
        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            color = self._LINE_MID if weight == "mid" else (self._LINE_STRONG if weight == "strong" else self._LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        # Start Y
        y = margin_t

        # --- HLAVIČKA ---
        # Titul a číslo faktury (vpravo nahoře)
        title_x = self._A4_W_PX - margin_r - self.mm(80)
        self._text(d,(title_x, y), "Faktura - Daňový doklad", font=self._f17b, fill=self._INK)
        y += self.mm(8)
        self._text(d,(title_x, y), f"{self._safe(self.invoice_number)}", label="Číslo dokladu: ", font=self._f13b, fill=self._INK, span_tag=span_tags.INVOICE_NUMBER, hard_undersampling=False)
        y += self.mm(10)
        
        # Logo/Jméno vlevo nahoře (pokud není logo, použije se jméno)
        self._text(d,(margin_l, margin_t), self._safe(self.supplier.name).upper(), font=self._f16b, fill=self._INK)

        y_sep = max(y, margin_t + self.mm(18)) + self.mm(5)

        # --- KUPUJÍCÍ A PRODÁVAJÍCÍ VEDLE SEBE ---
        col_sep = self.mm(10)
        col_w = (self._A4_W_PX - 2 * margin_l - col_sep) // 2
        
        # Prodávající (Levý sloupec)
        y_left = y_sep
        self._text(d,(margin_l, y_left), "Dodavatel (Prodávající):", font=self._f12b, fill=self._INK)
        y_left += self.mm(6)
        
        self._text(d,(margin_l, y_left), self._safe(self.supplier.name), font=self._f11b, fill=self._INK)
        y_left += self.mm(4)
        self._text(d,(margin_l, y_left), self._safe(self.supplier.address), font=self._f11, fill=self._INK)
        y_left += self.mm(4)
        self._text(d,(margin_l, y_left), label="IČ: ",text=f"{self._safe(self.supplier.register_id)}", font=self._f11, fill=self._INK, span_tag=span_tags.SUPPLIER_REGISTER_ID, hard_undersampling=False)
        y_left += self.mm(4)
        self._text(d,(margin_l, y_left), label="DIČ: ",text=f"{self._safe(self.supplier.tax_id)}", font=self._f11, fill=self._INK, span_tag=span_tags.SUPPLIER_TAX_ID, hard_undersampling=False)
        y_left += self.mm(4)

        # Kupující (Pravý sloupec)
        right_x = margin_l + col_w + col_sep
        y_right = y_sep
        self._text(d,(right_x, y_right), "Odběratel (Kupující):", font=self._f12b, fill=self._INK)
        y_right += self.mm(6)
        
        self._text(d,(right_x, y_right), self._safe(self.customer.name), font=self._f11b, fill=self._INK)
        y_right += self.mm(4)
        self._text(d,(right_x, y_right), self._safe(self.customer.address), font=self._f11, fill=self._INK)
        y_right += self.mm(4)
        self._text(d,(right_x, y_right), label="IČ: ", text=f"{self._safe(self.customer.register_id)}", font=self._f11, fill=self._INK, span_tag=span_tags.CUSTOMER_REGISTER_ID, hard_undersampling=False)
        y_right += self.mm(4)
        self._text(d,(right_x, y_right), label="DIČ: ",text=f"{self._safe(self.customer.tax_id)}", font=self._f11, fill=self._INK, span_tag=span_tags.CUSTOMER_TAX_ID, hard_undersampling=False)
        y_right += self.mm(4)

        # Nová startovací pozice Y
        y = max(y_left, y_right) + self.mm(5)

        hr(y, "mid")
        y += self.mm(3)

        # --- DATUMY A PLATBA (Pod sebou) ---
        kv_x = margin_l
        kv_y = y
        kv_label_w = self.mm(40) # užší sloupec pro popisky

        def kv_row(x:int, y_:int, label:str, value:str, before_value:str|None = None, bold:bool=True, tag: span_tags = span_tags.O, undersampling:bool = True)->None:
            x_label_end, _ = self._text(d,(x, y_), label, font=self._f11, fill=self._INK, span_tag=span_tags.O, hard_undersampling=undersampling)
            fontv = self._f11b if bold else self._f11

            self._text(d,(x_label_end, y_), value, font=fontv, fill=self._INK, span_tag=tag, hard_undersampling=undersampling)

        kv_row(kv_x,kv_y, "Datum vystavení:", self._safe(self.issue_date), tag = span_tags.ISSUE_DATE, undersampling=False);
        kv_y += self.mm(5)
        kv_row(kv_x,kv_y, "Datum splatnosti:", self._safe(self.due_date), tag = span_tags.DUE_DATE, undersampling=False);
        kv_y += self.mm(5)
        kv_row(kv_x,kv_y, "Způsob úhrady:", self._safe(self.payment.value), tag=span_tags.PAYMENT_TYPE, undersampling=False);
        kv_y += self.mm(8)
        kv_row(kv_x,kv_y, f"Bankovní spojení: {self.bank_account.name} ", value=f"{self._safe(self.bank_account_number)}", tag=span_tags.BANK_ACCOUNT_NUMBER, undersampling=False);
        kv_y += self.mm(5)
        kv_row(kv_x,kv_y, "IBAN:", self._safe(self.IBAN), tag=span_tags.IBAN, undersampling=False);
        kv_y += self.mm(5)
        kv_row(kv_x,kv_y, "Variabilní symbol:", self._safe(self.variable_symbol), tag=span_tags.VARIABLE_SYMBOL, undersampling=False);
        kv_y += self.mm(5)
        kv_row(kv_x,kv_y, "Konstantní symbol:", self._safe(self.const_symbol), tag=span_tags.CONST_SYMBOL, undersampling=False);
        kv_y += self.mm(5)
        kv_row(kv_x,kv_y, "BIC:", self._safe(self.bank_account.BIC), tag=span_tags.BIC, undersampling=False);
        kv_y += self.mm(5)

        y = kv_y + self.mm(5)
        hr(y, "mid")
        y += self.mm(5)

        # --- TABULKA POLOŽEK (Jednodušší) ---
        table_w = self._A4_W_PX - 2 * margin_l
        
        # Nové sloupce (Popis, Ks, Cena/ks s DPH, Celkem s DPH) - méně detailní
        headers = ["Popis zboží/služby", "Ks", "Jednotková cena bez DPH", "Celková cena s DPH"]
        # Nastavení šířek: 50% pro Popis, 10% pro Ks, 20% pro Jednotková cena, 20% pro Celkem
        col_ws = [0.30, 0.10, 0.30, 0.30]
        col_abs = [int(round(w * table_w)) for w in col_ws]
        x_cols = [margin_l]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        # hlavička tabulky
        head_h = self.mm(7)
        baseline = y + self.mm(2)
        
        for i, h in enumerate(headers):
            if i == 0:
                self._text(d,(x_cols[i] + 6, baseline), h, font=self._f11b, fill=self._INK)
            elif i == 1:
                # Ks - vystředěno
                self._draw_center(d, x_cols[i] + col_abs[i] / 2, baseline, h, self._f11b, self._INK)
            else:
                # Ostatní - doprava
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, baseline, h, self._f11b, self._INK)
        
        y += head_h
        d.line((margin_l, y, margin_l + table_w, y), fill=self._LINE_STRONG, width=2)

        # tělo tabulky
        row_h = self.mm(7)
        for it in self.items:
            y += row_h
            # oddělovací linka
            d.line((margin_l, y, margin_l + table_w, y), fill=self._LINE, width=1)

            cells = [
                self._safe(it.description),
                self._safe(it.quantity),
                self._fmt_money(it.ppu), # Nová hodnota
                self._fmt_money(it.price_with_vat), # Nová hodnota
            ]
            
            # vykreslení buněk
            y_text = y - row_h + self.mm(2)
            
            # 0 - popis (vlevo)
            self._text(d,(x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=self._INK)
            # 1 - ks (střed)
            self._draw_center(d, x_cols[1] + col_abs[1] / 2, y_text, cells[1], self._f11, self._INK)
            # 2..3 - doprava
            self._draw_right(d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], self._f11, self._INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], self._f11, self._INK)

        # Zvýraznění celkové ceny na konci tabulky
        y += self.mm(1.8)
        d.line((margin_l, y, margin_l + table_w, y), fill=self._LINE_STRONG, width=2)
        y += self.mm(1)
        foot_h = self.mm(8)

        # Celková cena
        self._text(d,(margin_l + 6, y + self.mm(2.5)), "CELKEM K ÚHRADĚ:", font=self._f12b, fill=self._INK, hard_undersampling=False)
        self._draw_right(d, margin_l + table_w - 6, y + self.mm(2.5), text=f"{self._fmt_money(self.calculated_total_price)}", end=f" {self.currency.value if hasattr(self.currency, 'value') else self.currency}", font=self._f13b, fill=self._INK, tag=span_tags.TOTAL, undersampling=False)
        y += foot_h

        hr(y, "strong") # Silná čára oddělující tabulku od souhrnu
        y += self.mm(5)

        # --- SOUHRNY DPH A POZNÁMKA ---
        
        # Souhrn DPH (Vlevo)
        vat_summary_x = margin_l
        vat_summary_w = self.mm(80)
        self._text(d,(vat_summary_x, y), "Přehled DPH:", font=self._f12b, fill=self._INK, hard_undersampling=False)
        y_vat = y + self.mm(6)
        
        for v in self.vat:
            x_vat, _ = self._text(d, (vat_summary_x, y_vat), label="Sazba " ,text=f"{self._safe(v.vat_percentage)}", end=" %:", span_tag=span_tags.VAT_PERCENTAGE, font=self._f11,
                                    fill=self._INK, hard_undersampling=False)
            
            x_vat, _ = self._text(d, (vat_summary_x+x_vat, y_vat), label="Základ " ,text=f"{self._fmt_money(v.vat_base)}", end=" Kč", span_tag=span_tags.VAT_BASE, font=self._f11
                                , fill=self._INK, hard_undersampling=False)

            x_vat, _ =self._text(d, (vat_summary_x+x_vat, y_vat), label="DPH ", text=f"{self._fmt_money(v.vat)}",span_tag=span_tags.VAT, fill=self._INK, font=self._f11, hard_undersampling=False)
            y_vat += self.mm(4)
        
        # Poznámka (Vpravo)
        note_x = margin_l
        y_vat += self.mm(5)
        self._text(d,(note_x, y_vat), "Poznámka:", font=self._f12b, fill=self._INK)
        self._text(d,(note_x, y_vat + self.mm(6)), "Děkujeme za Váš nákup!", font=self._f11, fill=self._INK)
        
        y = y_vat + self.mm(10)
        
        # --- PATIČKA ---
        bar_y = self._A4_H_PX - self.mm(12)
        hr(bar_y, "thin")
        self._text(d,(margin_l, bar_y + self.mm(2)), "Generováno pro účely testování OCR.", font=self._f10, fill=self._INK)
        self._draw_center(d, self._A4_W_PX / 2, bar_y + self.mm(2), "Strana 1 z 1", self._f10, self._INK)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        self._draw_right(d, self._A4_W_PX - margin_r, bar_y + self.mm(2), f"Tisk: {now_str}", self._f10, self._INK)

        # Uložení
        img = self.post_process(img)
        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=self._TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+self.mm(3)),word.tag.value, font=self._f10, fill=self._TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG", quality=100, subsampling=0)

        return True