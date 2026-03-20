import json
import random
from typing import Any, Dict, List, Tuple, final
from PIL import Image, ImageDraw, ImageFont
from decimal import Decimal

from numpy import add

from invoices_generator.templates.components.lorem.lorem_f import lorem_f
from invoices_generator.templates.components.lorem.lorem_e import lorem_e
from invoices_generator.templates.components.lorem.lorem_d import lorem_d
from invoices_generator.templates.components.lorem.lorem_c import lorem_c
from invoices_generator.templates.components.lorem.lorem_b import lorem_b
from invoices_generator.templates.components.total.total_b import total_b
from invoices_generator.templates.components.vats.vat_c import vat_c
from invoices_generator.templates.components.vats.vat_b import vat_b
from invoices_generator.templates.components.bank_details.bank_details_c import bank_details_c
from invoices_generator.templates.components.bodies.table_b import table_b
from invoices_generator.templates.components.bank_details.bank_details_b import bank_details_b
from invoices_generator.templates.components.lorem.lorem_a import lorem_a
from invoices_generator.templates.components.suppliers_customers.company_c import company_c
from invoices_generator.templates.components.suppliers_customers.company_b import company_b
from invoices_generator.templates.components.info.info_c import info_c
from invoices_generator.templates.components.info.info_b import info_b
from invoices_generator.templates.components.headers.header_a import header_a
from invoices_generator.templates.components.headers.header_b import header_b
from invoices_generator.templates.components.headers.header_c import header_c
from invoices_generator.templates.components.bank_details.bank_details_a import bank_details_a
from invoices_generator.templates.components.bodies.table_a import table_a
from invoices_generator.templates.components.info.info_a import info_a
from invoices_generator.templates.components.suppliers_customers.company_a import company_a
from invoices_generator.templates.components.total.total_a import total_a
from invoices_generator.templates.components.vats.vat_a import vat_a
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.relationship import relationship
from invoices_generator.utility.json_encoder import json_encoder

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.utils import safe, fmt_money


@final
class random_invoice(DInvoice):
    """
    Komplexní generátor faktur s vysokou vizuální variabilitou 
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Registrace dostupných variant komponent
        self.headers = [header_a, header_b, header_c]
        self.infos = [info_a, info_b, info_c]
        self.companies = [company_a, company_b, company_c]
        self.banks = [bank_details_a, bank_details_b,bank_details_c]
        self.tables = [table_a, table_b]
        self.vats = [vat_a, vat_b, vat_c]
        self.totals = [total_a, total_b]
        self.lorems = [lorem_a, lorem_b, lorem_c, lorem_d, lorem_e, lorem_f]

    def generate_img(self, output_path: str) -> bool:
        self.excluded = []
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)


        selected_lorems = random.sample(self.lorems, k=2)
        # 1. NÁHODNÝ VÝBĚR KOMPONENT
        comp = {
            "header": random.choice(self.headers),
            "info": random.choice(self.infos),
            "bank": random.choice(self.banks),
            "table": random.choice(self.tables),
            "vat": random.choice(self.vats),
            "total": random.choice(self.totals),
            "lorem": selected_lorems[0],
            "lorem2": selected_lorems[1],
            "supp": random.choice(self.companies),
            "cust": random.choice(self.companies)
        }

        # --- REÁLNÉ SCÉNÁŘE ROZLOŽENÍ ---
        # classic: standardní firemní faktura
        # sidebar: moderní služby (banka a info v postranním sloupci)
        # top_heavy: vše důležité nahoře v pásech (časté u e-shopů)
        # modern_split: čistý design, info a banka rozdělené v záhlaví
        # centered: minimalistický styl
        layout_type = random.choice(["classic", "sidebar", "top_heavy", "modern_split", "centered"])
        
        # Startovní pozice pro hlavičku
        curr_y = mm(random.randint(12, 18))
        curr_y = comp["header"].draw(self, d, mm(20), curr_y)

        if layout_type == "sidebar":
            # --- SIDEBAR STYLE ---
            # Adresy jdou pod sebe v levém sloupci, info a banka tvoří pravý blok
            addr_y = curr_y + mm(8)
            y_a = comp["supp"].draw(self, d, mm(20), addr_y, supplier=True)
            y_b = comp["cust"].draw(self, d, mm(20), y_a + mm(8), supplier=False)
            
            side_y = comp["info"].draw(self, d, mm(125), addr_y)
            side_y = comp["bank"].draw(self, d, mm(125), side_y + mm(5), width=mm(65))
            curr_y = max(y_b, side_y) + mm(10)

        elif layout_type == "top_heavy":
            # --- TOP-HEAVY (E-shop styl) ---
            # Info blok a Banka jsou vodorovně nahoře, pod nimi adresy vedle sebe
            curr_y += mm(5)
            y_info = comp["info"].draw(self, d, mm(20), curr_y)
            y_bank = comp["bank"].draw(self, d, mm(110), curr_y, width=mm(80))
            
            curr_y = max(y_info, y_bank) + mm(8)
            side_a, side_b = (mm(20), mm(115)) if random.random() > 0.5 else (mm(115), mm(20))
            y_a = comp["supp"].draw(self, d, side_a, curr_y, supplier=True)
            y_b = comp["cust"].draw(self, d, side_b, curr_y, supplier=False)
            curr_y = max(y_a, y_b) + mm(10)

        elif layout_type == "modern_split":
            # --- MODERN SPLIT ---
            # Info blok je vpravo nahoře u hlavičky, banka je až pod adresami přes celou šířku
            curr_y += mm(10)
            side_a, side_b = (mm(20), mm(115)) if random.random() > 0.5 else (mm(115), mm(20))
            y_a = comp["supp"].draw(self, d, side_a, curr_y, supplier=True)
            y_b = comp["cust"].draw(self, d, side_b, curr_y, supplier=False)
            curr_y = max(y_a, y_b) + mm(5)
            curr_y = comp["bank"].draw(self, d, mm(20), curr_y, width=mm(170)) + mm(8)

        elif layout_type == "centered":
            # --- CENTERED (Minimalist) ---
            # Vše v jednom sloupci uprostřed nebo mírně odsazené
            curr_y += mm(5)
            comp["lorem2"].draw(self, d, mm(105), curr_y)
            curr_y = comp["supp"].draw(self, d, mm(20), curr_y, supplier=True) + mm(5)
            curr_y = comp["cust"].draw(self, d, mm(20), curr_y, supplier=False) + mm(5)
            y_info = comp["info"].draw(self, d, mm(20), curr_y)
            y_bank = comp["bank"].draw(self, d, mm(110), curr_y, width=mm(80))
            curr_y = max(y_info, y_bank) + mm(10)

        else: # classic
            # --- CLASSIC (Standardní české rozvržení) ---
            header_x, lorem2_x = (mm(20), mm(115)) if random.random() > 0.5 else (mm(115), mm(20))
            lorem_y = comp["lorem2"].draw(self, d, lorem2_x, curr_y)
            curr_y = max(lorem_y, comp["info"].draw(self, d, header_x, curr_y + mm(5)))
            side_a, side_b = (mm(20), mm(115)) if random.random() > 0.5 else (mm(115), mm(20))
            y_a = comp["supp"].draw(self, d, side_a, curr_y + mm(10), supplier=True)
            y_b = comp["cust"].draw(self, d, side_b, curr_y + mm(10), supplier=False)
            curr_y = max(y_a, y_b) + mm(8)
            curr_y = comp["bank"].draw(self, d, mm(20), curr_y)

        # 5. ZÓNA: TABULKA (vždy uprostřed)
        curr_y = comp["table"].draw(self, d, mm(20), curr_y + mm(5))

        # 6. ZÓNA: PATIČKA (Finance)
        # Tady reálně vznikají dvě varianty: DPH pod tabulkou a Total vpravo, nebo vše v jednom sloupci
        foot_y = min(curr_y + mm(8), mm(260))
        
        end_y_vat = comp["vat"].draw(self, d, mm(20), foot_y)
        end_y_total = comp["total"].draw(self, d, mm(120), foot_y)
        curr_y = max(end_y_vat, end_y_total)


        # 7. ZÓNA: DOPLŇKY (Lorem ipsum / Razítko)
        if curr_y < mm(275):
            comp["lorem"].draw(self, d, mm(20), curr_y + mm(5))

        # --- DEBUG A EXPORT ---
        img = self.post_process(img)
        #debug_text = f"Layout: {layout_type} | H:{comp['header'].__name__} | T:{comp['table'].__name__}"
        #d_debug = ImageDraw.Draw(img)
        #d_debug.text((mm(5), mm(2)), text=debug_text, fill="red", font=self._f8)
        
        img.save(output_path, format="PNG")
        return True
