import random
from typing import final
from PIL import Image, ImageDraw

from invoices_generator.core.InvoiceComponent import InvoiceComponent
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from invoices_generator.templates.components.lorem.LoremF import LoremF
from invoices_generator.templates.components.lorem.LoremE import LoremE
from invoices_generator.templates.components.lorem.LoremD import LoremD
from invoices_generator.templates.components.lorem.LoremC import LoremC
from invoices_generator.templates.components.lorem.LoremB import LoremB
from invoices_generator.templates.components.total.TotalB import TotalB
from invoices_generator.templates.components.vats.VatC import VatC
from invoices_generator.templates.components.vats.VatB import VatB
from invoices_generator.templates.components.bank_details.BankDetailsC import BankDetailsC
from invoices_generator.templates.components.bodies.TableB import TableB
from invoices_generator.templates.components.bank_details.BankDetailsB import BankDetailsB
from invoices_generator.templates.components.lorem.LoremA import LoremA
from invoices_generator.templates.components.suppliers_customers.CompanyC import CompanyC
from invoices_generator.templates.components.suppliers_customers.CompanyB import CompanyB
from invoices_generator.templates.components.info.InfoC import InfoC
from invoices_generator.templates.components.info.InfoB import info_b
from invoices_generator.templates.components.headers.HeaderA import HeaderA
from invoices_generator.templates.components.headers.HeaderB import HeaderB
from invoices_generator.templates.components.headers.HeaderC import HeaderC
from invoices_generator.templates.components.bank_details.BankDetailsA import BankDetailsA
from invoices_generator.templates.components.bodies.TableA import TableA
from invoices_generator.templates.components.info.InfoA import InfoA
from invoices_generator.templates.components.suppliers_customers.CompanyA import CompanyA
from invoices_generator.templates.components.total.TotalA import TotalA
from invoices_generator.templates.components.vats.VatA import VatA

from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX, BG
from invoices_generator.utility.utils import mm


headers:list[InvoiceComponent] = [HeaderA, HeaderB, HeaderC]
infos:list[InvoiceComponent] = [InfoA, info_b, InfoC]
companies:list[InvoiceComponent] = [CompanyA, CompanyB, CompanyC]
banks:list[InvoiceComponent] = [BankDetailsA, BankDetailsB,BankDetailsC]
tables:list[InvoiceComponent] = [TableA, TableB]
vats:list[InvoiceComponent] = [VatA, VatB, VatC]
totals:list[InvoiceComponent] = [TotalA, TotalB]
lorems:list[InvoiceComponent] = [LoremA, LoremB, LoremC, LoremD, LoremE, LoremF]

@final
class RandomInvoice(InvoiceTemplate):
    """
    Komplexní generátor faktur s vysokou vizuální variabilitou 
    """

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)


        selected_lorems = random.sample(lorems, k=2)
        # 1. NÁHODNÝ VÝBĚR KOMPONENT
        comp = {
            "header": random.choice(headers),
            "info": random.choice(infos),
            "bank": random.choice(banks),
            "table": random.choice(tables),
            "vat": random.choice(vats),
            "total": random.choice(totals),
            "lorem": selected_lorems[0],
            "lorem2": selected_lorems[1],
            "supp": random.choice(companies),
            "cust": random.choice(companies)
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
        curr_y = comp["header"].render(textRenderer, data, invoice, mm(20), curr_y)

        if layout_type == "sidebar":
            # --- SIDEBAR STYLE ---
            # Adresy jdou pod sebe v levém sloupci, info a banka tvoří pravý blok
            addr_y = curr_y + mm(8)
            y_a = comp["supp"].render(textRenderer, data, invoice, mm(20), addr_y, supplier=True)
            y_b = comp["cust"].render(textRenderer, data, invoice, mm(20), y_a + mm(8), supplier=False)
            
            side_y = comp["info"].render(textRenderer, data, invoice, mm(125), addr_y)
            side_y = comp["bank"].render(textRenderer, data, invoice, mm(125), side_y + mm(5), width=mm(65))
            curr_y = max(y_b, side_y) + mm(10)

        elif layout_type == "top_heavy":
            # --- TOP-HEAVY (E-shop styl) ---
            # Info blok a Banka jsou vodorovně nahoře, pod nimi adresy vedle sebe
            curr_y += mm(5)
            y_info = comp["info"].render(textRenderer, data, invoice, mm(20), curr_y)
            y_bank = comp["bank"].render(textRenderer, data, invoice, mm(110), curr_y, width=mm(80))
            
            curr_y = max(y_info, y_bank) + mm(8)
            side_a, side_b = (mm(20), mm(115)) if random.random() > 0.5 else (mm(115), mm(20))
            y_a = comp["supp"].render(textRenderer, data, invoice, side_a, curr_y, supplier=True)
            y_b = comp["cust"].render(textRenderer, data, invoice, side_b, curr_y, supplier=False)
            curr_y = max(y_a, y_b) + mm(10)

        elif layout_type == "modern_split":
            # --- MODERN SPLIT ---
            # Info blok je vpravo nahoře u hlavičky, banka je až pod adresami přes celou šířku
            curr_y += mm(10)
            side_a, side_b = (mm(20), mm(115)) if random.random() > 0.5 else (mm(115), mm(20))
            y_a = comp["supp"].render(textRenderer, data, invoice, side_a, curr_y, supplier=True)
            y_b = comp["cust"].render(textRenderer, data, invoice, side_b, curr_y, supplier=False)
            curr_y = max(y_a, y_b) + mm(5)
            curr_y = comp["bank"].render(textRenderer, data, invoice, mm(20), curr_y, width=mm(170)) + mm(8)

        elif layout_type == "centered":
            # --- CENTERED (Minimalist) ---
            # Vše v jednom sloupci uprostřed nebo mírně odsazené
            curr_y += mm(5)
            comp["lorem2"].render(textRenderer, data, invoice, mm(105), curr_y)
            curr_y = comp["supp"].render(textRenderer, data, invoice, mm(20), curr_y, supplier=True) + mm(5)
            curr_y = comp["cust"].render(textRenderer, data, invoice, mm(20), curr_y, supplier=False) + mm(5)
            y_info = comp["info"].render(textRenderer, data, invoice, mm(20), curr_y)
            y_bank = comp["bank"].render(textRenderer, data, invoice, mm(110), curr_y, width=mm(80))
            curr_y = max(y_info, y_bank) + mm(10)

        else: # classic
            # --- CLASSIC (Standardní české rozvržení) ---
            header_x, lorem2_x = (mm(20), mm(115)) if random.random() > 0.5 else (mm(115), mm(20))
            lorem_y = comp["lorem2"].render(textRenderer, data, invoice, lorem2_x, curr_y)
            curr_y = max(lorem_y, comp["info"].render(textRenderer, data, invoice, header_x, curr_y + mm(5)))
            side_a, side_b = (mm(20), mm(115)) if random.random() > 0.5 else (mm(115), mm(20))
            y_a = comp["supp"].render(textRenderer, data, invoice, side_a, curr_y + mm(10), supplier=True)
            y_b = comp["cust"].render(textRenderer, data, invoice, side_b, curr_y + mm(10), supplier=False)
            curr_y = max(y_a, y_b) + mm(8)
            curr_y = comp["bank"].render(textRenderer, data, invoice, mm(20), curr_y)

        # 5. ZÓNA: TABULKA (vždy uprostřed)
        curr_y = comp["table"].render(textRenderer, data, invoice, mm(20), curr_y + mm(5))

        # 6. ZÓNA: PATIČKA (Finance)
        # Tady reálně vznikají dvě varianty: DPH pod tabulkou a Total vpravo, nebo vše v jednom sloupci
        foot_y = min(curr_y + mm(8), mm(260))
        
        end_y_vat = comp["vat"].render(textRenderer, data, invoice, mm(20), foot_y)
        end_y_total = comp["total"].render(textRenderer, data, invoice, mm(120), foot_y)
        curr_y = max(end_y_vat, end_y_total)


        # 7. ZÓNA: DOPLŇKY (Lorem ipsum / Razítko)
        if curr_y < mm(275):
            comp["lorem"].render(textRenderer, data, invoice, mm(20), curr_y + mm(5))

        
        invoice.image = img
        return True
