from datetime import datetime
import json
import random
from typing import Any, Dict, List, Tuple, final

from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal, ROUND_HALF_UP

from app.invoices.core.invoice import invoice
from app.invoices.utility.json_encoder import json_encoder

@final
class random_invoice(invoice):
    """
    Třída pro generování faktur s náhodným rozložením a pevnými i náhodnými popisky.
    Každá klíčová sekce faktury (dodavatel, odběratel, tabulka položek, atd.) je umístěna
    na náhodné pozici na stránce, s ohledem na to, aby se bloky nepřekrývaly.
    Také se náhodně vybírají popisky pro jednotlivé sekce.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Seznam pro ukládání klíčů vyloučených informací, které se nezobrazí.
        self.excluded: List[str] = []
        
        # Seznamy možných popisků pro randomizaci, teď obsahují více pevných konstant
        self.labels: Dict[str, Any] = {
            "supplier_labels": ["Dodavatel:", "Fakturováno od:", "Prodávající:", "Poskytovatel:"],
            "customer_labels": ["Odběratel:", "Fakturováno pro:", "Kupující:", "Zákazník:"],
            "universal": {
                "name": ["Jméno:", "Název firmy:"],
                "address": ["Adresa:", "Sídlo:", "Místo podnikání:"],
                "register_id": ["IČ:", "IČO:"],
                "tax_id": ["DIČ:", "VAT ID:"],
                "phone":["","Telefon:"]
            },
            "vat_summary": ["Přehled DPH:", "Souhrn DPH:", "Rozpis daně:", "VAT Summary:", "Sazby daně:", "VAT Rates:"],
            "total": ["Celkem k úhradě:", "Konečná cena:", "K zaplacení:", "Celková částka:", "Celkem:", "Total:"],
            "total_vat" : ["Celková daň:"],
            "invoice_info_labels": {
                "invoice_number": ["Faktura č.", "Číslo faktury:", "Doklad č."],
                "issue_date": ["Datum vystavení:", "Vystaveno:", "Datum:"],
                "due_date": ["Datum splatnosti:", "Splatnost do:", "Splatnost:"],
                "taxable_supply_date": ["Datum zdanitelného plnění"],
                "variable_symbol": ["Variabilní symbol:", "VS:", "Var. symb."],
                "const_symbol": ["Konstantní symbol:", "Const. symb.:"],
                "payment_method": ["Způsob úhrady:", "Platba:", "Metoda platby:"],
                "bank": ["Název banky:", "Banka:"],
                "bank_account": ["Bankovní účet:", "Účet:", "Číslo účtu:"],
            }
        }
        
        # Konfigurace pro dynamickou tabulku položek
        self.item_table_configs: List[Dict[str, Any]] = [
            {
                "headers": ["Popis", "Množství","Procentuální daň", "Jednotková cena", "Celkem"],
                "fields": ["description", "quantity","vat_percentage", "ppu", "price_with_vat"],
                "col_widths": [0.3,0.1, 0.1, 0.25, 0.25]
            },
            {
                "headers": ["Popis", "Množství", "Daň %","Jednotková cena", "Jednotka", "Celkem"],
                "fields": ["description", "quantity","vat_percentage", "ppu", "unit_of_measure", "price_with_vat"],
                "col_widths": [0.25, 0.1, 0.1, 0.2, 0.1, 0.25]
            },
            {
                "headers": ["Položka", "Ks", "Cena bez DPH", "DPH", "DPH %", "Cena s DPH"],
                "fields": ["description", "quantity", "price_without_vat", "vat", "vat_percentage", "price_with_vat"],
                "col_widths": [0.4, 0.1, 0.1,0.1, 0.1, 0.2]
            }
        ]

    def to_json(self) -> Any:
        # Používá standardní serializaci dat, aby byl výstup konzistentní
        data = dict(issue_date=self.issue_date, due_date=self.due_date, taxable_supply_date=self.taxable_supply_date,
                    payment=self.payment.value, bank=self.bank_account, IBAN=self.IBAN, bank_account_number=self.bank_account_number, 
                    variable_symbol=self.variable_symbol, const_symbol=self.const_symbol, 
                    supplier = self.supplier, customer = self.customer,
                    items = self.items, vat_items = self.vat, rounding = self.rounding,
                    total_price = self.calculated_total_price, total_vat = self.calculated_total_vat, currency = self.currency,
                    invoice_number = self.invoice_number)

        j_data: Dict[str, Any] = json.loads(json.dumps(data, cls=json_encoder, ensure_ascii=False))

        if self.excluded:
            # Rozdělí vyloučené klíče na ty, co se týkají položek a zbytek
            item_fields_to_exclude = {field.split('.')[1] for field in self.excluded if field.startswith('items.')}
            other_fields_to_exclude = [field for field in self.excluded if not field.startswith('items.')]

            # Zpracování ostatních (ne-položkových) vyloučených polí
            for field_path in other_fields_to_exclude:
                keys = field_path.split('.')
                current_dict = j_data
                for i, key in enumerate(keys):
                    if key in current_dict:
                        if i == len(keys) - 1:
                            if key in ["total_vat", "total_price", "rounding"]:
                                current_dict[key] = None
                            else:
                                current_dict[key] = ""
                        else:
                            current_dict = current_dict[key]
                    else:
                        break
            
            # Zpracování vyloučených polí v tabulce položek
            for item in j_data.get('items', []):
                for field in item_fields_to_exclude:
                    if field in item:
                        if field in ["description", "unit_of_measure"]:
                            item[field] = ""
                        else:
                            item[field] = None

            j_data["total_vat"] = None

        return j_data

    def generate_img(self, output_path: str) -> bool:
        """
        Hlavní metoda, která generuje fakturu s náhodným uspořádáním.
        Jednotlivé bloky se náhodně rozmístí, aby se nepřekrývaly.
        """
        self.excluded = []
        margin = self.mm(25)
        
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        # Definice bloků s jejich přibližnými rozměry (šířka, výška)
        blocks = [
            {"id": "supplier", "width": self.mm(80), "height": self.mm(40), "draw_func": self._draw_supplier_block},
            {"id": "customer", "width": self.mm(80), "height": self.mm(40), "draw_func": self._draw_customer_block},
            {"id": "invoice_info", "width": self.mm(80), "height": self.mm(45), "draw_func": self._draw_invoice_info_block},
            {"id": "vat_summary", "width": self.mm(80), "height": self.mm(30 + len(self.vat) * 5), "draw_func": self._draw_vat_summary_block},
            {"id": "items_table", "width": self.mm(160), "height": self.mm(15 + len(self.items) * 6.5), "draw_func": self._draw_items_table_block},
            {"id": "total", "width": self.mm(80), "height": self.mm(20), "draw_func": self._draw_total_block},
            #{"id": "total_vat", "width": self.mm(80), "height": self.mm(20), "draw_func": self._draw_total_vat_block},
            {"id": "bank_account", "width": self.mm(80), "height": self.mm(20), "draw_func": self._draw_bank_account_block}
        ]
        
        random.shuffle(blocks)
        placed_blocks = []
        
        y = self.mm(8) 
        # Pokus o umístění každého bloku na náhodné místo bez překrývání
        for block in blocks:
            placed = False
            attempts = 0
            while not placed and attempts < 200:
                x = random.randint(margin, self._A4_W_PX - margin - block["width"])
                
                new_rect = (x, y, x + block["width"], y + block["height"])
                overlap = False
                
                for placed_block in placed_blocks:
                    placed_rect = placed_block["rect"]
                    if (new_rect[0] < placed_rect[2] and new_rect[2] > placed_rect[0] and
                        new_rect[1] < placed_rect[3] and new_rect[3] > placed_rect[1]):
                        overlap = True
                        break
                
                if not overlap:
                    block["rect"] = new_rect
                    block["draw_func"](d, x, y)
                    placed_blocks.append(block)
                    placed = True
                attempts += 1
            y += block["height"]
            if not placed:
                print(f"Nepodařilo se umístit blok {block['id']} po {attempts} pokusech. Možná je stránka příliš plná.")
        
        self.post_process(img).save(output_path, format="PNG", quality=100, subsampling=0)
        return True

    def _draw_supplier_block(self, d: ImageDraw.ImageDraw, x: int, y: int) -> None:
        """Vykreslí blok s informacemi o dodavateli s náhodným vyloučením polí."""
        d.text((x, y), random.choice(self.labels["supplier_labels"]), font=self._f12b, fill=self._INK)
        y_offset = self.mm(6)
        
        # Vytvoří seznam polí, která se mají zobrazit
        fields = [
            ("supplier.name", self.supplier.name, self.labels['universal']['name']),
            ("supplier.phone", self.supplier.phone, self.labels['universal']['phone']),
            ("supplier.register_id", self.supplier.register_id, self.labels['universal']['register_id']),
            ("supplier.tax_id", self.supplier.tax_id, self.labels['universal']['tax_id']),
        ]

        supplier_lines: List[str] = [f"{random.choice(self.labels['universal']['address'])} {self._safe(self.supplier.address)}",]
        for field, value, label in fields:
            if random.choice([True, False]):
                supplier_lines.append(f"{random.choice(label)} {self._safe(value)}")
            else:
                self.excluded.append(field)
        
        random.shuffle(supplier_lines)
        
        current_y = y + y_offset
        for line in supplier_lines:
            d.text((x, current_y), line, font=self._f11, fill=self._INK)
            current_y += self.mm(5)
        
    def _draw_customer_block(self, d: ImageDraw.ImageDraw, x: int, y: int) -> None:
        """Vykreslí blok s informacemi o zákazníkovi s náhodným vyloučením polí."""
        d.text((x, y), random.choice(self.labels["customer_labels"]), font=self._f12b, fill=self._INK)
        y_offset = self.mm(6)
        
        # Vytvoří seznam polí, která se mají zobrazit
        fields = [
            ("customer.name", self.customer.name, self.labels['universal']['name']),
            ("customer.phone", self.customer.phone, self.labels['universal']['phone']),
            ("customer.register_id", self.customer.register_id, self.labels['universal']['register_id']),
            ("customer.tax_id", self.customer.tax_id, self.labels['universal']['tax_id']),
        ]

        cust_lines: List[str] = [f"{random.choice(self.labels['universal']['address'])} {self._safe(self.customer.address)}"]
        for field, value, label in fields:
            if random.choice([True, False]):
                cust_lines.append(f"{random.choice(label)} {self._safe(value)}")
            else:
                self.excluded.append(field)
        
        random.shuffle(cust_lines)
        
        current_y = y + y_offset
        for line in cust_lines:
            d.text((x, current_y), line, font=self._f11, fill=self._INK)
            current_y += self.mm(5)

    def _draw_invoice_info_block(self, d: ImageDraw.ImageDraw, x: int, y: int) -> None:
        """Vykreslí blok s informacemi o faktuře (číslo, datumy atd.) s náhodným vyloučením polí."""
        d.text((x, y), f"{random.choice(self.labels['invoice_info_labels']['invoice_number'])} {self._safe(self.invoice_number)}", font=self._f13b, fill=self._INK)
        y_offset = self.mm(8)
        
        # Definice všech možných informací o faktuře s jejich klíči
        info_lines_data: List[Tuple[str, str]] = [
            ("issue_date", f"{random.choice(self.labels['invoice_info_labels']['issue_date'])} {self._safe(self.issue_date)}"),
            ("due_date", f"{random.choice(self.labels['invoice_info_labels']['due_date'])} {self._safe(self.due_date)}"),
            ("taxable_supply_date", f"{random.choice(self.labels['invoice_info_labels']['taxable_supply_date'])} {self._safe(self.taxable_supply_date)}"),
            ("variable_symbol", f"{random.choice(self.labels['invoice_info_labels']['variable_symbol'])} {self._safe(self.variable_symbol)}"),
            ("const_symbol", f"{random.choice(self.labels['invoice_info_labels']['const_symbol'])} {self._safe(self.const_symbol)}"),
            ("payment", f"{random.choice(self.labels['invoice_info_labels']['payment_method'])} {self._safe(self.payment.value)}")
        ]
        
        selected_info_lines_data: List[str] = []
        for field, line in info_lines_data:
            if random.choice([True, False]):
                selected_info_lines_data.append(line)
            else:
                self.excluded.append(field)

        random.shuffle(selected_info_lines_data)
        
        current_y = y + y_offset
        for line in selected_info_lines_data:
            d.text((x, current_y), line, font=self._f11, fill=self._INK)
            current_y += self.mm(5)

    def _draw_vat_summary_block(self, d: ImageDraw.ImageDraw, x: int, y: int) -> None:
        """Vykreslí blok se souhrnem DPH."""
        d.text((x, y), random.choice(self.labels["vat_summary"]), font=self._f12b, fill=self._INK)
        y += self.mm(5)
        for v in self.vat:
            vat_line = f"DPH {self._safe(v.vat_percentage)}% | Základ: {self._fmt_money(v.vat_base)} | Daň: {self._fmt_money(v.vat)}"
            d.text((x, y), vat_line, font=self._f11, fill=self._INK)
            y += self.mm(5)
    
    def _draw_bank_account_block(self, d: ImageDraw.ImageDraw, x: int, y: int) -> None:
        """Vykreslí blok s bankovním spojením."""
        d.text((x, y), random.choice(["Bankovní spojení:", "Bankovní účet:"]), font=self._f12b, fill=self._INK)
        y_offset = self.mm(6)
        
        fields = [
            ("bank.name", self.bank_account.name, self.labels['invoice_info_labels']['bank']),
            ("bank_account_number", self.bank_account_number, self.labels['invoice_info_labels']['bank_account']),
            ("IBAN", self.IBAN, ["IBAN:"]),
            ("bank.BIC", self.IBAN, ["BIC:"])
        ]
        
        bank_lines: List[str] = []
        for field, value, label in fields:
            if random.choice([True, False]):
                bank_lines.append(f"{random.choice(label)} {self._safe(value)}")
            else:
                self.excluded.append(field)
                
        random.shuffle(bank_lines)
        
        current_y = y + y_offset
        for line in bank_lines:
            d.text((x, current_y), line, font=self._f11, fill=self._INK)
            current_y += self.mm(5)

    def _draw_items_table_block(self, d: ImageDraw.ImageDraw, x: int, y: int) -> None:
        """Vykreslí tabulku s položkami faktury s náhodným uspořádáním sloupců."""
        table_w = self.mm(160)
        config = random.choice(self.item_table_configs)
        
        # Zajištění, že alespoň jeden sloupec se zobrazí, nejlépe "description"
        all_columns = list(zip(config["headers"], config["fields"], config["col_widths"]))
        
        shuffled_columns = random.sample(all_columns, random.randint(2, len(all_columns)))
        
        # Zajištění, že sloupec "Popis" je vždy přítomen pro čitelnost
        desc_col = next((c for c in all_columns if c[1] == "description"), None)
        if desc_col and desc_col not in shuffled_columns:
            shuffled_columns.append(desc_col)

        # Určení vyloučených polí a jejich přidání do seznamu self.excluded
        shuffled_fields_set = {f[1] for f in shuffled_columns}
        all_fields_set = set(['description','quantity','ppu','price_without_vat', 'vat_percentage','vat','price_with_vat'])
        excluded_fields = all_fields_set - shuffled_fields_set
        for field in excluded_fields:
            self.excluded.append(f"items.{field}")

        shuffled_headers, shuffled_fields, shuffled_col_ws = zip(*shuffled_columns)
        
        col_abs = [int(round(w * table_w)) for w in shuffled_col_ws]
        x_cols = [x]
        for wv in col_abs[:-1]:
            x_cols.append(x_cols[-1] + wv)

        y_head = y + self.mm(2)
        for i, h in enumerate(shuffled_headers):
            if i == 0:
                d.text((x_cols[i] + 6, y_head), h, font=self._f11b, fill=self._INK)
            else:
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, y_head, h, font=self._f11b, fill=self._INK)
        y += self.mm(7)
        d.line([(x, y), (x + table_w, y)], fill=self._LINE_STRONG, width=2)
        
        row_h = self.mm(6.5)
        for it in self.items:
            y += row_h
            d.line([(x, y), (x + table_w, y)], fill=self._LINE, width=1)
            
            cells: List[str] = []
            for field in shuffled_fields:
                if field == "ppu":
                    cells.append(self._fmt_money(it.ppu))
                elif field == "price_with_vat":
                    cells.append(self._fmt_money(it.price_with_vat))
                elif field == "vat":
                    cells.append(self._fmt_money(it.vat))
                elif field == "price_without_vat":
                    cells.append(self._fmt_money(it.price_without_vat))
                elif field == "vat_percentage":
                    cells.append(f"{self._safe(it.vat_percentage)}%")
                elif field == "unit_of_measure":
                    cells.append(self._safe("ks"))
                else:
                    cells.append(self._safe(getattr(it, field)))
            
            y_text = y - row_h + self.mm(2)
            d.text((x_cols[0] + 6, y_text), cells[0], font=self._f11, fill=self._INK)
            for i in range(1, len(cells)):
                self._draw_right(d, x_cols[i] + col_abs[i] - 6, y_text, cells[i], self._f11, fill=self._INK)

    def _draw_total_block(self, d: ImageDraw.ImageDraw, x: int, y: int) -> None:
        """Vykreslí blok s konečnou celkovou částkou."""
        d.text((x, y), random.choice(self.labels["total"]), font=self._f13b, fill=self._INK)
        y += self.mm(8)
        total_txt = f"{self._fmt_money(self.calculated_total_price)} {self.currency.value}"
        d.text((x, y), total_txt, font=self._f17b, fill=self._INK)

    def _draw_total_vat_block(self, d: ImageDraw.ImageDraw, x: int, y: int)-> None:
        d.text((x, y), random.choice(self.labels["total_vat"]), font=self._f13b, fill=self._INK)
        y += self.mm(8)
        total_txt = f"{self._fmt_money(self.calculated_total_vat)} {self.currency.value}"
        d.text((x, y), total_txt, font=self._f17b, fill=self._INK)
