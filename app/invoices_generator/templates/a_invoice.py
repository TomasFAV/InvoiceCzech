from datetime import datetime
from typing import final

from PIL import Image, ImageDraw, ImageFont


from invoice_annotator.utils.GRelationship import GRelationship
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words
from invoices_generator.utility.utils import safe, fmt_money




@final
class a_invoice(DInvoice):

    

    def generate_img(self, output_path: str) -> bool:
        # Okraje (zjednodušené pro nový vzhled)
        margin_l = mm(20)
        margin_r = mm(20)
        margin_t = mm(15)
        
        # Plátno
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        # Pomocné čáry (funkce hr)
        def hr(y: int, weight: str = "mid", x0: int | None = None, x1: int | None = None) -> None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            d.line([(x0, y), (x1, y)], fill=color, width=3 if weight == "strong" else 2)

        # Start Y
        y = margin_t

        # --- HLAVIČKA ---
        # Titul a číslo faktury (vpravo nahoře)
        title_x = self._A4_W_PX - margin_r - mm(80)
        self._text(d,(title_x, y), "Faktura - Daňový doklad", font=self._f17b, fill=INK)
        y += mm(8)
        self._text(d,(title_x, y), f"{safe(self.invoice_number)}", label="Číslo dokladu: ", font=self._f13b, fill=INK, span_tag=span_tags.INVOICE_NUMBER)
        y += mm(10)
        
        # Logo/Jméno vlevo nahoře (pokud není logo, použije se jméno)
        self._text(d,(margin_l, margin_t), safe(self.supplier.name).upper(), font=self._f16b, fill=INK)

        y_sep = max(y, margin_t + mm(18)) + mm(5)

        # --- KUPUJÍCÍ A PRODÁVAJÍCÍ VEDLE SEBE ---
        col_sep = mm(10)
        col_w = (self._A4_W_PX - 2 * margin_l - col_sep) // 2
        
        # Prodávající (Levý sloupec)
        y_left = y_sep
        self._text(d,(margin_l, y_left), "Dodavatel (Prodávající):", font=self._f12b, fill=INK)
        y_left += mm(6)
        
        self._text(d,(margin_l, y_left), safe(self.supplier.name), font=self._f11b, fill=INK)
        y_left += mm(4)
        self._text(d,(margin_l, y_left), safe(self.supplier.address), font=self._f11, fill=INK)
        y_left += mm(4)
        self._text(d,(margin_l, y_left), label="IČ: ",text=f"{safe(self.supplier.register_id)}", font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_REGISTER_ID)
        y_left += mm(4)
        self._text(d,(margin_l, y_left), label="DIČ: ",text=f"{safe(self.supplier.tax_id)}", font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_TAX_ID)
        y_left += mm(4)

        # Kupující (Pravý sloupec)
        right_x = margin_l + col_w + col_sep
        y_right = y_sep
        self._text(d,(right_x, y_right), "Odběratel (Kupující):", font=self._f12b, fill=INK)
        y_right += mm(6)
        
        self._text(d,(right_x, y_right), safe(self.customer.name), font=self._f11b, fill=INK)
        y_right += mm(4)
        self._text(d,(right_x, y_right), safe(self.customer.address), font=self._f11, fill=INK)
        y_right += mm(4)
        self._text(d,(right_x, y_right), label="IČ: ", text=f"{safe(self.customer.register_id)}", font=self._f11, fill=INK, span_tag=span_tags.CUSTOMER_REGISTER_ID)
        y_right += mm(4)
        self._text(d,(right_x, y_right), label="DIČ: ",text=f"{safe(self.customer.tax_id)}", font=self._f11, fill=INK, span_tag=span_tags.CUSTOMER_TAX_ID)
        y_right += mm(4)

        # Nová startovací pozice Y
        y = max(y_left, y_right) + mm(5)

        hr(y, "mid")
        y += mm(3)

        # --- DATUMY A PLATBA (Pod sebou) ---
        kv_x = margin_l
        kv_y = y
        kv_label_w = mm(40) # užší sloupec pro popisky

        def kv_row(x:int, y_:int, label:str, value:str, before_value:str|None = None, bold:bool=True, tag: span_tags = span_tags.O, undersampling:bool = True)->None:
            x_label_end, _ = self._text(d,(x, y_), label, font=self._f11, fill=INK, span_tag=span_tags.O)
            fontv = self._f11b if bold else self._f11

            self._text(d,(x_label_end, y_), value, font=fontv, fill=INK, span_tag=tag)

        kv_row(kv_x,kv_y, "Datum vystavení:", safe(self.issue_date), tag = span_tags.ISSUE_DATE)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "Datum splatnosti:", safe(self.due_date), tag = span_tags.DUE_DATE)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "Způsob úhrady:", safe(self.payment_type), tag=span_tags.PAYMENT_TYPE)
        kv_y += mm(8)
        kv_row(kv_x,kv_y, f"Bankovní spojení: {self.bank_account.name} ", value=f"{safe(self.bank_account_number)}", tag=span_tags.BANK_ACCOUNT_NUMBER);
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "IBAN:", safe(self.IBAN), tag=span_tags.IBAN)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "Variabilní symbol:", safe(self.variable_symbol), tag=span_tags.VARIABLE_SYMBOL)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "Konstantní symbol:", safe(self.const_symbol), tag=span_tags.CONST_SYMBOL)
        kv_y += mm(5)
        kv_row(kv_x,kv_y, "BIC:", safe(self.bank_account.BIC), tag=span_tags.BIC)
        kv_y += mm(5)

        y = kv_y + mm(5)
        hr(y, "mid")
        y +=mm(5)

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
        head_h = mm(7)
        baseline = y +mm(2)
        
        for i, h in enumerate(headers):
            if i == 0:
                self._text(d,(x_cols[i] + 6, baseline), h, font=self._f11b, fill=INK, must_have_same_width=True)
            elif i == 1:
                # Ks - vystředěno
                self._draw_center(d, x_cols[i] + col_abs[i] / 2, baseline, h, self._f11b, INK, must_have_same_width=True)
            else:
                # Ostatní - doprava
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, baseline, h, self._f11b,INK, must_have_same_width=True)
        
        y += head_h
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)

        # tělo tabulky
        row_h = mm(7)
        for it in self.items:
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
            self._text(d,(x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=INK)
            # 1 - ks (střed)
            self._draw_center(d, x_cols[1] + col_abs[1] / 2, y_text, cells[1], self._f11, INK)
            # 2..3 - doprava
            self._draw_right(d, x_cols[2] + col_abs[2] - 6, y_text, cells[2], self._f11, INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 6, y_text, cells[3], self._f11, INK)

        # Zvýraznění celkové ceny na konci tabulky
        y += mm(1.8)
        d.line((margin_l, y, margin_l + table_w, y), fill=LINE_STRONG, width=2)
        y += mm(1)
        foot_h = mm(8)

        # Celková cena
        self._text(d,(margin_l + 6, y + mm(2.5)), "CELKEM K ÚHRADĚ:", font=self._f12b, fill=INK)
        self._draw_right(d, margin_l + table_w - 6, y + mm(2.5), text=f"{fmt_money(self.calculated_total_price)}", end=f" {self.currency.value if hasattr(self.currency, 'value') else self.currency}", font=self._f13b, fill=INK, span_tag=span_tags.TOTAL)
        y += foot_h

        hr(y, "strong") # Silná čára oddělující tabulku od souhrnu
        y += mm(5)

        # --- SOUHRNY DPH A POZNÁMKA ---
        
        # Souhrn DPH (Vlevo)
        vat_summary_x = margin_l
        vat_summary_w = mm(80)
        self._text(d,(vat_summary_x, y), "Přehled DPH:", font=self._f12b, fill=INK)
        y_vat = y + mm(6)
        
        for v in self.vat:
            x_vat, percentage_id = self._text(d, (vat_summary_x, y_vat), label="Sazba " ,text=f"{safe(v.vat_percentage)}", end=" %:", span_tag=span_tags.VAT_PERCENTAGE, font=self._f11,
                                    fill=INK)
            
            x_vat, base_id = self._text(d, (vat_summary_x+x_vat, y_vat), label="Základ " ,text=f"{fmt_money(v.vat_base)}", end=" Kč", span_tag=span_tags.VAT_BASE, font=self._f11
                                , fill=INK)

            x_vat, vat_id =self._text(d, (vat_summary_x+x_vat, y_vat), label="DPH ", text=f"{fmt_money(v.vat)}",span_tag=span_tags.VAT, fill=INK, font=self._f11)

            self.append_relationship(GRelationship(None, base_id, percentage_id, relationship_types.BASE_OF))
            self.append_relationship(GRelationship(None, vat_id, percentage_id, relationship_types.VAT_OF))

            y_vat += mm(4)
        
        # Poznámka (Vpravo)
        note_x = margin_l
        y_vat += mm(5)
        self._text(d,(note_x, y_vat), "Poznámka:", font=self._f12b, fill=INK)
        self._text(d,(note_x, y_vat + mm(6)), "Děkujeme za Váš nákup!", font=self._f11, fill=INK)
        
        y = y_vat + mm(10)
        
        # --- PATIČKA ---
        bar_y = self._A4_H_PX - mm(12)
        hr(bar_y, "thin")
        self._text(d,(margin_l, bar_y + mm(2)), "Generováno pro účely testování OCR.", font=self._f10, fill=INK)
        self._draw_center(d, self._A4_W_PX / 2, bar_y + mm(2), "Strana 1 z 1", self._f10, INK)
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
        self._draw_right(d, self._A4_W_PX - margin_r, bar_y + mm(2), f"Tisk: {now_str}", self._f10, INK)

        # Uložení
        img = self.post_process(img)
        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+self.mm(3)),word.tag.value, font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG", quality=100, subsampling=0)
        return True
