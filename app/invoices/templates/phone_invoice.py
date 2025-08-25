import json
import random
from typing import Any, Dict, final
from app.invoices.core.invoice import invoice
from datetime import datetime, timedelta
from typing import Optional, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

from app.invoices.utility.json_encoder import json_encoder

@final
class phone_invoice(invoice):

    def to_json(self)->Any:

        data:Dict[str, Any] = dict(issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date=self.taxable_supply_date,
                    payment=self.payment.value, bank=self.bank_account, bank_account_number=self.bank_account_number, IBAN = "", 
                    variable_symbol=self.variable_symbol, const_symbol=self.const_symbol, 
                    supplier = self.supplier, customer = self.customer,
                    items = self.items, vat_items = self.vat, rounding = self.rounding,
                    total_price = self.calculated_total_price, total_vat = self.calculated_total_vat, currency = self.currency,
                    invoice_number = self.invoice_number)

        #zrušení vazeb na instance bank, zákazníků, dodavatelů
        j_data:Dict[str, Any] = json.loads(json.dumps(data, cls = json_encoder, ensure_ascii=False))

        #Mazání informací, které nejsou z faktury dostupné
        j_data["bank"]["BIC"] = ""
        j_data["IBAN"] = ""
        j_data["bank"]["name"] = ""

        j_data["total_vat"] = None

        j_data["items"] = {}
        for item in j_data["vat_items"]:
            item["vat_base"] = None

        return j_data


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
        margin_l = self.mm(15)
        margin_r = self.mm(15)
        margin_t = self.mm(15)
        margin_b = self.mm(15)

        # Vytvoření plátna
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        # Pomocné funkce pro čáry
        def hr(y:float, weight:str="mid", x0:Optional[int]=None, x1:Optional[int]=None)->None:
            x0 = margin_l if x0 is None else x0
            x1 = self._A4_W_PX - margin_r if x1 is None else x1
            if weight == "strong":
                color, width = self._LINE_STRONG, 3
            elif weight == "mid":
                color, width = self._LINE_MID, 2
            else:
                color, width = self._LINE, 1
            d.line([(x0, y), (x1, y)], fill=color, width=width)

        y = margin_t

        # --- HLAVIČKA S T-MOBILE LOGEM ---
        # T-Mobile logo vlevo
        d.text((margin_l, y), "T", font=self._f48b, fill=self._TMOBILE_PINK)
        
        # Čárový kód vpravo
        barcode_text = "2 25912770 5 014"
        barcode_x = self._A4_W_PX - margin_r - self.mm(40)
        d.text((barcode_x, y), barcode_text, font=self._f10, fill=self._INK)
        d.text((barcode_x, y + self.mm(4)), "|||||||||||||||||| 01", font=self._f10, fill=self._INK)

        y += self.mm(20)

        # Jemná oddělovací čára
        hr(y, "thin")
        y += self.mm(8)

        # --- HLAVNÍ OBSAH - DVA SLOUPCE ---
        col_gap = self.mm(20)
        page_w = self._A4_W_PX - margin_l - margin_r
        col_w = (page_w - col_gap) // 2
        left_x = margin_l
        right_x = margin_l + col_w + col_gap

        # LEVÝ SLOUPEC - Dodavatel
        d.text((left_x, y), "Dodavatel", font=self._f11b, fill=self._INK)
        y_left = y + self.mm(6)

        company_lines = [
            self.supplier.name,
            self.supplier.address,
            f"IČO: {self.supplier.register_id}",
            f"Telefon: {self.supplier.phone}",
            f"DIČ: {self.supplier.tax_id}"
        ]

        for line in company_lines:
            d.text((left_x, y_left), line, font=self._f10, fill=self._INK)
            y_left += self.mm(4.5)

        # PRAVÝ SLOUPEC - Vyúčtování služeb
        d.text((right_x, y), "Vyúčtování služeb", font=self._f16b, fill=self._INK)
        d.text((right_x, y + self.mm(6)), random_period(), font=self._f11, fill=self._MUTED)
        
        y_right = y + self.mm(15)
        
        # Zákazník v rámečku
        d.text((right_x, y_right), "Zákazník", font=self._f11b, fill=self._INK)
        y_right += self.mm(6)
        
        # Rámeček pro zákazníka
        box_h = self.mm(25)
        d.rectangle((right_x, y_right, right_x + col_w, y_right + box_h), 
                   outline=self._LINE_MID, width=2, fill=None)
        
        # Obsah rámečku
        padding = self.mm(3)
        customer_lines = [
            self.customer.name,
            self.customer.address,
            self.customer.city,
            f"IČ: {self.customer.register_id} DIČ: {self.customer.tax_id}"
        ]
        
        y_customer = y_right + padding
        for line in customer_lines:
            d.text((right_x + padding, y_customer), line, font=self._f10, fill=self._INK)
            y_customer += self.mm(4.5)

        # Posun Y pro další sekce
        y = max(y_left, y_right + box_h) + self.mm(10)

        # --- PLATEBNÍ ÚDAJE - DVA SLOUPCE ---
        # Levý sloupec - Údaje pro platbu
        
        draw_box(left_x-self.mm(5), y-self.mm(5), left_x + self.mm(75), self.mm(50), border_color=self._TMOBILE_PINK)

        d.text((left_x, y), "Údaje pro platbu", font=self._f11b, fill=self._INK)
        y_payment = y + self.mm(6)

        payment_items = [
            ("Bankovní účet", str(self.bank_account_number)),
            ("Konstantní symbol", str(self.const_symbol)),
            ("Variabilní symbol", str(self.variable_symbol)),
            ("Specifický symbol", ""),
            ("Datum úhrady", str(self.due_date)),
            ("Způsob úhrady", str(self.payment.value)),
        ]

        for label, value in payment_items:
            d.text((left_x, y_payment), label, font=self._f10, fill=self._INK)
            d.text((left_x + self.mm(35), y_payment), value, font=self._f11, fill=self._INK)
            y_payment += self.mm(5)

        # Celková částka
        y_payment += self.mm(3)
        d.text((left_x, y_payment), "Celkem k úhradě", font=self._f12b, fill=self._INK)
        total_text = f"{self._fmt_money(self.calculated_total_price)} Kč"
        d.text((left_x + self.mm(35), y_payment), total_text, font=self._f12b, fill=self._INK)

        # Pravý sloupec - Další údaje
        y_right = y + self.mm(6)
        
        payment_items = [
            ("Daňový doklad číslo", str(self.invoice_number)),
            ("Datum uskutečnění zdan. plnění", str(self.taxable_supply_date)),
            ("Datum vystavení", str(self.issue_date)),
            ("Datum splatnosti", str(self.due_date)),
        ]

        for label, value in payment_items:
            d.text((right_x, y_right), label, font=self._f10, fill=self._INK)
            d.text((right_x + self.mm(45), y_right), value, font=self._f11, fill=self._INK)
            y_right += self.mm(5)

        y = max(y_payment + self.mm(8), y_right) + self.mm(5)

        # --- ČÍSLO SLUŽBY ---
        service_text = f"{self.customer.phone} / 7 GB Plus"
        self._draw_center(d, self._A4_W_PX // 2, y, service_text, self._f14b, self._INK)
        y += self.mm(5)

        # --- TABULKA ÚČTOVANÝCH POLOŽEK ---
        # Hlavička tabulky
        table_w = page_w
        d.rectangle((margin_l, y, margin_l + table_w, y + self.mm(8)), 
                   outline=None, fill=self._BG)
        
        d.text((margin_l + self.mm(3), y + self.mm(2.5)), 
               "Účtované položky (detail za skupiny přehled služeb)", 
               font=self._f10, fill=self._INK)
        y += self.mm(8)

        table_items: list[tuple[str, str]] = [
            ("Celková za služby bez DPH", f"{self._fmt_money(self.calculated_total_price_without_vat)} Kč"),
            ("Zaokrouhlení", f"{self._fmt_money(self.rounding)} Kč"),
        ]
        
        # Přidat všechny VAT sazby
        for v in self.vat:
            vat_label = f"DPH ({self._safe(v.vat_percentage)}%)"
            vat_value = f"{self._fmt_money(v.vat)} Kč"
            table_items.append((vat_label, vat_value))
        
        # Celková částka
        table_items.append(("Celková za služby včetně DPH", f"{self._fmt_money(self.calculated_total_price)} Kč"))

        for item_label, item_value in table_items:
            hr(y, "thin")
            d.text((margin_l + self.mm(3), y + self.mm(3)), item_label, font=self._f10, fill=self._INK)
            self._draw_right(d, margin_l + table_w - self.mm(3), y + self.mm(3), item_value, self._f10, self._INK)
            y += self.mm(7)

        hr(y, "thin")
        y += self.mm(10)

        # --- CELKOVÁ ČÁSTKA ---
        d.rectangle((margin_l, y, margin_l + table_w, y + self.mm(12)), 
                   outline=None, fill=self._BG)
        total_final = f"Celkem k úhradě   {self._fmt_money(self.calculated_total_price)} Kč"
        self._draw_center(d, self._A4_W_PX // 2, y + self.mm(4), total_final, self._f16b, self._INK)
        y += self.mm(20)

        # --- UPOZORNĚNÍ ---
        notice_text = ("Z provozních důvodů je k 1. 1. 2025 dočasně pozastaven přechod pro EU roaming "
                      "(Dočasných směrný nařízení EU). Maximální cena připojení za ochránený výkon "
                      "rozhodnutím EK má rozhodnou činnosti službu a do 1. 1. 2025 automaticky na "
                      "55,5 EUR za mesiac službu společnost na vyžadované pozici službu. Pro více "
                      "informací o roamingu EU navštivte naše webové stránky či volejte nás na 603 603 603.")

        # Pozadí pro upozornění
        notice_h = self.mm(20)
        d.rectangle((margin_l, y, margin_l + table_w, y + notice_h), 
                   outline=None, fill=(255, 248, 220))
        
        # Barevný levý okraj
        d.rectangle((margin_l, y, margin_l + self.mm(1), y + notice_h), 
                   fill=self._TMOBILE_PINK)

        # Ikona "i"
        d.ellipse((margin_l + self.mm(3), y + self.mm(2), 
                  margin_l + self.mm(8), y + self.mm(7)), 
                 fill=self._TMOBILE_PINK)
        d.text((margin_l + self.mm(4.5), y + self.mm(2.5)), "i", font=self._f11b, fill=self._BG)

        # Text upozornění (zalamování)
        words = notice_text.split()
        lines = []
        current_line = ""
        max_width = table_w - self.mm(15)

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if self._text_width(d, test_line, self._f10) < max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        y_notice = y + self.mm(2)
        for line in lines:
            d.text((margin_l + self.mm(10), y_notice), line, font=self._f10, fill=self._INK)
            y_notice += self.mm(3.5)

        y += notice_h + self.mm(5)

        # --- PATIČKA ---
        hr(y, "thin")
        y += self.mm(3)

        # Stránka
        self._draw_right(d, self._A4_W_PX - margin_r, y, "Stránka 1/1", self._f10, self._INK)
        
        # Malý text
        footer_text = ("Registrace k dani z přidané hodnoty dle zákona ČPNI, I.10 279 665 a tel s DPTI "
                      "a stal společností představitaující u Finančního úřadu zastupovaného")
        d.text((margin_l, y + self.mm(4)), footer_text, font=self._f10, fill=self._MUTED)

        # Uložení
        #img.show()
        self.post_process(img).save(output_path, format="PNG", quality=100, subsampling=0)
        return True
