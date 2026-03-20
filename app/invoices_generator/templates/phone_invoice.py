import random
from typing import final

from invoice_annotator.utils.GRelationship import GRelationship
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice
from datetime import datetime, timedelta
from typing import Optional, final

from PIL import Image, ImageDraw


from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, TMOBILE_PINK
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words
from invoices_generator.utility.utils import safe, fmt_money


@final
class phone_invoice(DInvoice):

    

    def generate_img(self, output_path: str) -> bool:
        """Generování T-Mobile faktury jako obrázku"""
        
        def random_period(start_year: int = 2000, end_year: int = 2025) -> str:
            # Náhodné datum od
            start_date = datetime(
                year=random.randint(start_year, end_year),
                month=random.randint(1, 12),
                day=random.randint(1, 28)  # aby nevznikaly problémy s únorem
            )
            # Náhodné přičtení dní (1 až 1000 dní po start_date)
            end_date = start_date + timedelta(days=random.randint(1, 1000))

            # Formátování do evropského stylu DD.MM.RRRR
            start_str = start_date.strftime("%d.%m.%Y")
            end_str = end_date.strftime("%d.%m.%Y")

            return f"za období {start_str} - {end_str}"

        # Pomocná funkce pro obdélníky s pozadím
        def draw_box(x:float, y:float, width:float, height:float, bg_color:Optional[tuple[int,int,int]]=None, border_color:Optional[tuple[int,int,int]]=None, border_width:int=1)->None:
            if bg_color:
                d.rectangle((x, y, x + width, y + height), fill=bg_color)
            if border_color:
                d.rectangle((x, y, x + width, y + height), outline=border_color, width=border_width)

        # Okraje
        margin_l = mm(15)
        margin_r = mm(15)
        margin_t = mm(15)
        margin_b = mm(15)

        # Vytvoření plátna
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        # Pomocné funkce pro čáry
        def hr(y:float, weight:str="mid", x0:Optional[int]=None, x1:Optional[int]=None)->None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            if weight == "strong":
                color, width = LINE_STRONG, 3
            elif weight == "mid":
                color, width = LINE_MID, 2
            else:
                color, width = LINE, 1
            d.line([(x0, y), (x1, y)], fill=color, width=width)

        y = margin_t

        # --- HLAVIČKA S T-MOBILE LOGEM ---
        # T-Mobile logo vlevo
        self._text(d,(margin_l, y), "T", font=self._f48b, fill=TMOBILE_PINK)
        
        # Čárový kód vpravo
        barcode_text = "2 25912770 5 014"
        barcode_x = self._A4_W_PX - margin_r - mm(40)
        self._text(d,(barcode_x, y), barcode_text, font=self._f10, fill=INK)
        self._text(d,(barcode_x, y + mm(4)), "|||||||||||||||||| 01", font=self._f10, fill=INK)

        y += mm(20)

        # Jemná oddělovací čára
        hr(y, "thin")
        y += mm(8)

        # --- HLAVNÍ OBSAH - DVA SLOUPCE ---
        col_gap = mm(20)
        page_w = self._A4_W_PX - margin_l - margin_r
        col_w = (page_w - col_gap) // 2
        left_x = margin_l
        right_x = margin_l + col_w + col_gap

        # LEVÝ SLOUPEC - Dodavatel
        self._text(d,(left_x, y), "Dodavatel", font=self._f11b, fill=INK)
        y_left = y + mm(6)

        self._text(d,(left_x, y_left), text=self.supplier.name, font=self._f10, fill=INK)
        y_left += mm(4.5)

        self._text(d,(left_x, y_left), text=self.supplier.address, font=self._f10, fill=INK)
        y_left += mm(4.5)

        self._text(d,(left_x, y_left), label="IČO: ", text=f"{self.supplier.register_id}", font=self._f10, fill=INK, span_tag=span_tags.SUPPLIER_REGISTER_ID)
        y_left += mm(4.5)

        self._text(d,(left_x, y_left), text=f"Telefon: {self.supplier.phone}", font=self._f10, fill=INK)
        y_left += mm(4.5)

        self._text(d,(left_x, y_left), label="DIČ", text=f"{self.supplier.tax_id}", font=self._f10, fill=INK, span_tag=span_tags.SUPPLIER_TAX_ID)
        y_left += mm(4.5)

        # PRAVÝ SLOUPEC - Vyúčtování služeb
        self._text(d,(right_x, y), "Vyúčtování služeb", font=self._f16b, fill=INK)
        self._text(d,(right_x, y + mm(6)), random_period(), font=self._f11, fill=MUTED)
        
        y_right = y + mm(15)
        
        # Zákazník v rámečku
        self._text(d,(right_x, y_right), "Zákazník", font=self._f11b, fill=INK)
        y_right += mm(6)
        
        # Rámeček pro zákazníka
        box_h = mm(25)
        d.rectangle((right_x, y_right, right_x + col_w, y_right + box_h), 
                outline=LINE_MID, width=2, fill=None)
        
        # Obsah rámečku
        padding = mm(3)
        customer_lines = [
            self.customer.name,
            f"{self.customer.street}, {self.customer.zip}",
            self.customer.city,
        ]
        
        y_customer = y_right + padding
        for line in customer_lines:
            self._text(d,(right_x + padding, y_customer), line, font=self._f10, fill=INK)
            y_customer += mm(4.5)

        self._text(d,(right_x + padding, y_customer), label="IČ: ", text=f"{self.customer.register_id}", font=self._f10, fill=INK, span_tag=span_tags.CUSTOMER_REGISTER_ID)
        y_customer += mm(4.5)

        self._text(d,(right_x + padding, y_customer), label="DIČ: ", text=f"{self.customer.tax_id}", font=self._f10, fill=INK, span_tag=span_tags.CUSTOMER_TAX_ID)
        y_customer += mm(4.5)

        # Posun Y pro další sekce
        y = max(y_left, y_right + box_h) + mm(10)

        # --- PLATEBNÍ ÚDAJE - DVA SLOUPCE ---
        # Levý sloupec - Údaje pro platbu
        
        draw_box(left_x-mm(5), y-mm(5), left_x + mm(75), mm(50), border_color=TMOBILE_PINK)

        self._text(d,(left_x, y), "Údaje pro platbu", font=self._f11b, fill=INK)
        y_payment = y + mm(6)

        payment_items = [
            ("Bankovní účet", str(self.bank_account_number), span_tags.BANK_ACCOUNT_NUMBER),
            ("Konstantní symbol", str(self.const_symbol), span_tags.CONST_SYMBOL),
            ("Variabilní symbol", str(self.variable_symbol), span_tags.VARIABLE_SYMBOL),
            ("Specifický symbol", "", span_tags.O),
            ("Datum úhrady", str(self.due_date), span_tags.DUE_DATE),
            ("Způsob úhrady", str(self.payment_type), span_tags.PAYMENT_TYPE),
        ]

        for label, value, tag in payment_items:
            self._text(d,(left_x, y_payment), text=label, font=self._f10, fill=INK)
            self._text(d,(left_x + mm(35), y_payment), text=value, font=self._f11, fill=INK, span_tag=tag)
            y_payment += mm(5)

        # Celková částka
        y_payment += mm(3)
        new_x = self._text(d,(left_x, y_payment), "Celkem k úhradě", font=self._f12b, fill=INK)[0]
        total_text = f"{fmt_money(self.calculated_total_price)}"
        self._text(d,(new_x + mm(5), y_payment), text=total_text, end=" Kč", font=self._f12b, fill=INK, span_tag=span_tags.TOTAL)

        # Pravý sloupec - Další údaje
        y_right = y + mm(6)
        
        payment_items = [
            ("Daňový doklad číslo", str(self.invoice_number), span_tags.INVOICE_NUMBER),
            ("Datum uskutečnění zdan. plnění", str(self.taxable_supply_date), span_tags.TAXABLE_SUPPLY_DATE),
            ("Datum vystavení", str(self.issue_date), span_tags.ISSUE_DATE),
            ("Datum splatnosti", str(self.due_date), span_tags.DUE_DATE),
        ]

        for label, value, tag in payment_items:
            self._text(d,(right_x, y_right), text=label, font=self._f10, fill=INK)
            self._text(d,(right_x + mm(45), y_right), text=value, font=self._f11, fill=INK, span_tag=tag)
            y_right += mm(5)

        y = max(y_payment + mm(8), y_right) + mm(5)

        # --- ČÍSLO SLUŽBY ---
        service_text = f"{self.customer.phone} / 7 GB Plus"
        self._draw_center(d, self._A4_W_PX // 2, y, service_text, self._f14b, INK)
        y += mm(5)

        # --- TABULKA ÚČTOVANÝCH POLOŽEK ---
        # Hlavička tabulky
        table_w = page_w
        d.rectangle((margin_l, y, margin_l + table_w, y + mm(8)), 
                    outline=None, fill=BG)
        
        self._text(d,(margin_l + mm(3), y + mm(2.5)), 
                "Účtované položky (detail za skupiny přehled služeb)", 
                font=self._f10, fill=INK)
        y += mm(8)

        table_items: list[tuple[str, str]] = [
            ("Celková za služby bez DPH", f"{fmt_money(self.calculated_total_price_without_vat)} Kč"),
            ("Zaokrouhlení", f"{fmt_money(self.rounding)} Kč"),
        ]
        
        for item_label, item_value in table_items:
            hr(y, "thin")
            self._text(d,(margin_l + mm(3), y + mm(3)), item_label, font=self._f10, fill=INK)
            self._draw_right(d, margin_l + table_w - mm(3), y + mm(3), item_value, self._f10, INK)
            y += mm(7)

        for v in self.vat:
            hr(y, "thin")
            _, percentage_id = self._text(d,(margin_l + mm(3), y + mm(3)), label="DPH (", text=f"{safe(v.vat_percentage)}", end="%)", font=self._f10, fill=INK, span_tag=span_tags.VAT_PERCENTAGE)
            _, vat_id = self._draw_right(d, margin_l + table_w - mm(3), y + mm(3), text=f"{fmt_money(v.vat)}",end="Kč", font=self._f10, fill=INK, span_tag=span_tags.VAT)
            
            self.append_relationship(GRelationship(None, vat_id, percentage_id, relationship_types.BASE_OF))
            
            y += mm(7)

        hr(y, "thin")
        self._text(d,(margin_l + mm(3), y + mm(3)), text="Celková za služby včetně DPH", font=self._f10, fill=INK)
        self._draw_right(d, margin_l + table_w - mm(3), y + mm(3), text=f"{fmt_money(self.calculated_total_price)}", end="Kč", font=self._f10, fill=INK, span_tag=span_tags.TOTAL)
        y += mm(7)

        hr(y, "thin")
        y += mm(10)

        # --- CELKOVÁ ČÁSTKA ---
        d.rectangle((margin_l, y, margin_l + table_w, y + mm(12)), 
                    outline=None, fill=BG)
        total_final = f"Celkem k úhradě   {fmt_money(self.calculated_total_price)} Kč"
        self._draw_center(d, self._A4_W_PX // 2, y + mm(4), label="Celkem k úhradě ",text=f"{fmt_money(self.calculated_total_price)}",end=" Kč", font=self._f16b, fill=INK, span_tag=span_tags.TOTAL)
        y += mm(20)

        # --- UPOZORNĚNÍ ---
        notice_text = ("Z provozních důvodů je k 1. 1. 2025 dočasně pozastaven přechod pro EU roaming "
                    "(Dočasných směrný nařízení EU). Maximální cena připojení za ochránený výkon "
                    "rozhodnutím EK má rozhodnou činnosti službu a do 1. 1. 2025 automaticky na "
                    "55,5 EUR za mesiac službu společnost na vyžadované pozici službu. Pro více "
                    "informací o roamingu EU navštivte naše webové stránky či volejte nás na 603 603 603.")

        # Pozadí pro upozornění
        notice_h = mm(20)
        d.rectangle((margin_l, y, margin_l + table_w, y + notice_h), 
                    outline=None, fill=(255, 248, 220))
        
        # Barevný levý okraj
        d.rectangle((margin_l, y, margin_l + mm(1), y + notice_h), 
                    fill=TMOBILE_PINK)

        # Ikona "i"
        d.ellipse((margin_l + mm(3), y + mm(2), 
                    margin_l + mm(8), y + mm(7)), 
                    fill=TMOBILE_PINK)
        self._text(d,(margin_l + mm(4.5), y + mm(2.5)), "i", font=self._f11b, fill=BG)

        # Text upozornění (zalamování)
        words = notice_text.split()
        lines = []
        current_line = ""
        max_width = table_w - mm(15)

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if text_width(test_line, self._f10) < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        y_notice = y + mm(2)
        for line in lines:
            self._text(d,(margin_l + mm(10), y_notice), line, font=self._f10, fill=INK)
            y_notice += mm(3.5)

        y += notice_h + mm(5)

        # --- PATIČKA ---
        hr(y, "thin")
        y += mm(3)

        # Stránka
        self._draw_right(d, self._A4_W_PX - margin_r, y, "Stránka 1/1", self._f10, INK)
        
        # Malý text
        footer_text = ("Registrace k dani z přidané hodnoty dle zákona ČPNI, I.10 279 665 a tel s DPTI "
                    "a stal společností představitaující u Finančního úřadu zastupovaného")
        self._text(d,(margin_l, y + mm(4)), footer_text, font=self._f10, fill=MUTED)

        # Uložení
        #img.show()
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+mm(3)),word.tag.value, font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")
        return True
