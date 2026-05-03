from dataclasses import dataclass
from datetime import date, timedelta
import json
import os
import random
import secrets

from tqdm.auto import tqdm
from contextlib import ExitStack


from common.invoice.renderers.InvoicePostProcessor import InvoicePostProcessor
from data_generator.DataGenerator import DataGenerator
from common.data.Bank import Bank
from common.invoice.processors.IEProcessors.DonutIEProcessor import DonutIEConfig
from common.invoice.processors.IEProcessors.LayoutLMV3IEProcessor import LayoutLMV3IEConfig
from common.invoice.processors.InvoiceExporter import InvoiceExporter
from common.invoice.OperationResult import OperationResult
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.invoice.renderers.InvoiceRenderer import InvoiceRenderer
from invoices_generator.templates.AudiInvoice import AudiInvoice 
from invoices_generator.templates.OreaHotelInvoice import OreaHotelInvoice
from invoices_generator.templates.MartinusInvoice import MartinusInvoice
from common.data.Company import Company
from common.enumerates.SpanTag import SPAN_TAGS_TO_IGNORE, SpanTag
from common.data.InvoiceItem import InvoiceItem
from invoices_generator.templates.AlzaInvoice import AlzaInvoice
from invoices_generator.templates.GeneralInvoice import GeneralInvoice
from invoices_generator.templates.PhoneInvoice import PhoneInvoice
from invoices_generator.templates.PostInvoice import PostInvoice
from invoices_generator.templates.RestaurantReceipt import RestaurantReceipt
from invoices_generator.templates.StoreReceipt import StoreReceipt
from invoices_generator.templates.ClassicInvoice import ClassicInvoice
from invoices_generator.templates.ModernInvoice import ModernInvoice
from invoices_generator.templates.ColorfullInvoice import ColorfullInvoice
from invoices_generator.templates.CompactInvoice import CompactInvoice
from invoices_generator.templates.AInvoice import AInvoice
from invoices_generator.templates.SimpleInvoice import SimpleInvoice
from invoices_generator.templates.InvertedInvoice import InvertedInvoice
from invoices_generator.templates.RandomInvoice import RandomInvoice
from invoices_generator.templates.KnihyDobrovskyInvoice import KnihyDobrovskyInvoice
from invoices_generator.templates.FlexibeeInvoice import FlexibeeInvoice

from common.data.invoice_consts import *


@dataclass
class InvoiceGenerator:
    
    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################


    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################

    def generate_company()->Company:

        is_company:bool = True if random.randrange(0, 4) > 1 else False

        company_name:str
        street_name:str = street_names[random.randrange(0, len(street_names))]
        zip_code:str = f"{random.randint(0, 99999):05d}" #peticiferne cislo
        city_name:str = city_names[random.randrange(0, len(city_names))]
        
        if random.random() < 0.5:
            phone = "+420" if random.random() < 0.5 else ""
            phone += f"{random.randint(000000000, 999999999):09d}"
        else:
            phone = "+420" if random.random() < 0.5 else ""
            phone += f"{random.randint(000, 999):03d} {random.randint(000, 999):03d} {random.randint(000, 999):03d}"
        
        email = f"{secrets.token_hex(int(random.random()*10))}@gmail.com"
        
        register_id:str
        tax_id:str
        type:CompanyType

        if(is_company):

            company_name = company_names[random.randrange(0, len(company_names))]
            register_id = f"{random.randint(00000000, 99999999):08d}" #osmimistne cislo
            tax_id = "" if random.randrange(0,1) == 1 else (f"CZ{register_id}")
            type = company_types[random.randrange(0, len(company_types))]
        
        else: 
            
            company_name = person_names[random.randrange(0, len(person_names))]
            register_id = "" if random.randrange(0, 4) > 1 else f"{random.randint(00000000, 99999999):08d}" #osmimistne cislo
            tax_id = ""
            type = CompanyType.INDIVIDUAL

        return Company(name=company_name,
                        street=street_name,
                        zip=zip_code,
                        city=city_name,
                        phone=phone,
                        register_id=register_id,
                        tax_id=tax_id,
                        type=type,
                        mail=email)
    
    def generate_bank_account(bank:Bank) -> tuple[str, str]:
        # základní číslo účtu (1–10 číslic), doplním na 10
        account_number = f"{random.randint(1, 9999999999):09d}"

        # předčíslí (nepovinné), tady dám třeba náhodně 0–3 číslic
        prefix = f"{random.randint(0, 999999):03d}"

        if random.random() < 0.25:
            number = f"{prefix}-{account_number}/{bank.code}"
        else:
            number = f"{account_number}/{bank.code}"

        # vytvoření IBANu (CZ + 2 číslice + kód banky + číslo účtu)
        check_digits = f"{random.randint(10, 99)}"
        iban = f"CZ{check_digits}{bank.code}{account_number:0>16}"  # vždy 24 znaků
        
        if random.random() < 0.25:
            n = 4
            iban = " ".join([iban[i:i+n] for i in range(0, len(iban), n)])

        return (number, iban)

    def generate_item()->InvoiceItem:
        quantity:int = random.randrange(1, 5)
        ppu = random.randrange(100,1000)

        price_without_vat = ppu*quantity
        vat_percentage = vat_percentages[random.randrange(0, len(vat_percentages))]

        vat = price_without_vat * (vat_percentage/100)
        price_with_vat = price_without_vat + vat
        name = item_names[random.randrange(0, len(item_names))]

        return InvoiceItem(description=name, quantity=quantity, ppu=ppu,
                            price_without_vat=price_without_vat, vat=vat,
                            vat_percentage=vat_percentage, price_with_vat=price_with_vat)


    def generate_items(max_quantity:int = 7)->tuple[list[InvoiceItem], float, float]:
        items:list[InvoiceItem] = list()
        if max_quantity != 1:
            quantity = random.randrange(1, max_quantity)
        else:
            quantity = max_quantity

        total_price:float = 0
        total_vat:float = 0


        for _ in range(quantity):
            item = DataGenerator.generate_item()
            items.append(item)

            total_price += item.price_with_vat
            total_vat += item.vat

        return (items, total_price, total_vat)

    def generate_invoice_number() -> str:
        year = random.choice([2024, 2025, 2026])
        short_year = str(year)[2:]
        month = random.randint(1, 12)
        # Pořadové číslo s náhodnou délkou (někdo má 001, někdo 00001)
        num_val = random.randrange(1, 10000)
        padding = random.choice([3, 4, 5, 6])
        num = f"{num_val:0{padding}d}"
        
        # Seznam formátů, které se vyskytují v praxi
        formats = [
            f"{year}{num}",                    # 20260001
            f"{year}{month:02d}{num}",         # 2026020001
            f"{year}-{num}",                   # 2026-0001
            f"{num}/{short_year}",             # 0001/26
            f"{num}/{year}",                   # 0001/2026
            f"{year}/{num}",                   # 2026/0001
            f"{short_year}{month:02d}{num}",   # 26020001
            f"FV{year}{num}",                  # FV20260001 (prefix bez mezery)
            f"INV-{year}-{num}",               # INV-2026-0001
            f"{year}.{num}",                   # 2026.0001
            f"{year} {num}",                   # 2026 0001
            f"{random.choice(['S', 'P', 'X'])}{year}{num}" # S20260001 (kódy středisek)
        ]
        
        # Občas tam necháme i náhodný extrém (velké číslo)
        if random.random() < 0.05:
            return f"{random.randrange(0, 99999999)}"
            
        return random.choice(formats)
    
    
    def generate_variable_symbol(invoice_number: str) -> str:

        if random.random() < 0.1:
            return str(random.randint(100, 9999999999))

        # 1. Odstranění všeho, co není číslo
        clean_number = "".join(filter(str.isdigit, invoice_number))
        
        # 2. Odstranění úvodních nul (banky je stejně zahazují)
        clean_number = clean_number.lstrip('0')
        
        # 3. Omezení na 10 znaků (vezmeme konec čísla, ten bývá unikátní)
        if len(clean_number) > 10:
            clean_number = clean_number[-10:]
            
        # 4. Pokud po vyčištění nic nezbylo, vygenerujeme náhodné číslo
        if not clean_number:
            clean_number = str(random.randint(100, 9999999999))
            
        return clean_number

    def generate_const_symbol()->str:
        ran = random.randrange(0,4)

        if(ran>1):
            return ""
        else:
            return f"{random.randrange(0, 9999):04d}"
    
    def generate_invoice_dates() -> tuple[str, str, str]:
        today = date.today()
        
        # náhodné datum vystavení během posledních X dní
        random_offset = random.randint(0, 1440)
        issue_date_obj = today - timedelta(days=random_offset)

        date_format = random.choice(date_formats)

        def fmt(d: date) -> str:
            return d.strftime(date_format)

        issue_date = fmt(issue_date_obj)

        # taxable supply date (buď stejné, nebo posun -3 až +5 dní)
        if random.choice([True, False]):
            taxable_supply_date = issue_date
        else:
            shift = random.randint(-3, 5)
            taxable_supply_date = fmt(issue_date_obj + timedelta(days=shift))

        # due date (issue_date + splatnost)
        due_date = fmt(issue_date_obj + timedelta(days=random.randint(7, 28)))

        return (issue_date, taxable_supply_date, due_date)

    def generate_folder(folder: str, count: int, templates:list[type[InvoiceTemplate]]) -> None:
        renderer: InvoiceRenderer = InvoiceRenderer()
        post_processor: InvoicePostProcessor = InvoicePostProcessor()
        exporter: InvoiceExporter = InvoiceExporter()

        # Definice cest k souborům
        paths = {
            "donut": f"app/data/{folder}/metadata_donut.jsonl",
            "layoutlm": f"app/data/{folder}/metadata_layoutlmv3.jsonl",
            "coco": f"app/data/{folder}/metadata_coco.json",
            "yolo": f"app/data/{folder}/labels/"
        }

        os.makedirs(paths["yolo"], exist_ok=True)

        # Výpočet celkového počtu pro tqdm (počet iterací * počet tříd faktur)
        total_steps = count * len(templates)

        # Otevřeme všechny soubory a spustíme progress bar
        with ExitStack() as stack:
            f_donut = stack.enter_context(open(paths["donut"], "w", encoding="utf-8"))
            f_layout = stack.enter_context(open(paths["layoutlm"], "w", encoding="utf-8"))

            pbar = tqdm(total=total_steps, desc=f"Generování faktur ({folder})", unit="img")

            for _ in range(count):
                for template in templates:
                    data:InvoiceData = DataGenerator.generate_invoice_data()

                    file_name = f"{template.__name__}_{data.invoice_number.replace("/","")}.png"
                    img_folder = f"app/data/{folder}/images/"
                    img_path = os.path.join(img_folder, file_name) 

                    os.makedirs(img_folder, exist_ok=True)

                    render_result: OperationResult = renderer.render(data, template)
                    post_process_result: OperationResult = post_processor.post_process(render_result.passed_value) #augmentuje fakturu(bboxy + obrázek)

                    # --- 2. Generování obrázku ---
                    if render_result.ok and post_process_result:
                        
                        invoice: Invoice = render_result.passed_value
                        invoice.image.save(img_path)

                        # --- 3. Zápis do DONUT (JSONL) ---
                        donut_gt = {"gt_parse": exporter.export_donut(invoice, data, DonutIEConfig.FROM_INVOICE_DATA_WITH_CHECK)}
                        donut_output = {
                            "file_name": file_name,
                            "ground_truth": donut_gt
                        }
                        f_donut.write(json.dumps(donut_output, ensure_ascii=False) + "\n")

                        # --- 4. Zápis do LAYOUTLMv3 (JSONL) ---
                        layout_data = exporter.export_layoutlmv3(invoice, LayoutLMV3IEConfig.WITH_TESSERACT)
                        layout_output = {
                            "file_name": file_name,
                            "data": layout_data
                        }
                        f_layout.write(json.dumps(layout_output, ensure_ascii=False) + "\n")

                        # --- 5. Sběr dat pro COCO ---
                        coco_data = exporter.export_coco(invoice, paths["coco"], file_name)
                        with open(paths["coco"], "w", encoding="utf-8") as f_coco:
                            f_coco.write(json.dumps(coco_data, ensure_ascii=False, indent=4))
                        
                        # --- 6. YOLO formát ---
                        yolo_data = exporter.export_yolo(invoice)
                        with open(paths["yolo"]+f"{template.__name__}_{data.invoice_number.replace("/","")}.txt", "w", encoding="utf-8") as f_yolo:
                            f_yolo.write(yolo_data)



                    # Update progress baru po každé faktuře
                    pbar.update(1)

            pbar.close()


        print(f"\nHotovo! Metadata uložena v {folder}:")
        print(f" - Donut: {paths['donut']}")
        print(f" - LayoutLMv3: {paths['layoutlm']}")
        print(f" - COCO: {paths['coco']}")
                
    def generate(train_count:int, test_count:int, validation_count:int, random_template:bool = False)->bool:

        invoice_classes: list[type[InvoiceTemplate]] = [
                AInvoice,
                AlzaInvoice,
                AudiInvoice,
                ClassicInvoice,
                ColorfullInvoice,
                CompactInvoice,
                FlexibeeInvoice,
                GeneralInvoice,
                InvertedInvoice,
                KnihyDobrovskyInvoice,
                MartinusInvoice,
                ModernInvoice,
                OreaHotelInvoice,
                PhoneInvoice,
                PostInvoice,
                RestaurantReceipt,
                SimpleInvoice,
                StoreReceipt,
                
                #audi_invoice,
                #orea_hotel_invoice,
                #martinus_invoice,
                
                #flexibee_invoice,
                # flexibee_invoice,

                #alza_invoice,
                # alza_invoice,
                #general_invoice,
                # general_invoice,
                # general_invoice,
                
                #phone_invoice,
                # phone_invoice,
                #post_invoice,
                # post_invoice,
                # post_invoice,
                
                #restaurant_receipt,
                #store_receipt,
                #classic_invoice,
                # classic_invoice,
                #modern_invoice,
                
                #colorful_invoice, 
                #compact_invoice,
                # compact_invoice,
                #a_invoice,
                # a_invoice,
                
                #simple_invoice,
                #inverted_invoice,
                # inverted_invoice,
                #knihy_dobrovsky,
                # knihy_dobrovsky,
                #random_invoice,
                # random_invoice,
                
                #RandomInvoice,
                #RandomInvoice,
                #RandomInvoice,
                #RandomInvoice,
                #RandomInvoice,
                
                #RandomInvoice,
                #RandomInvoice,
                #RandomInvoice,
                #RandomInvoice,
                #RandomInvoice,

                #RandomInvoice,
                #RandomInvoice,
        ]

        if random_template:
            invoice_classes: list[type[InvoiceTemplate]] = [RandomInvoice]

        if(train_count>0):
            InvoiceGenerator.generate_folder("train", train_count,invoice_classes)

        if(test_count>0):
            InvoiceGenerator.generate_folder("test", test_count, invoice_classes)

        if(validation_count>0):
            InvoiceGenerator.generate_folder("validation", validation_count, invoice_classes)


        class_names = "\n\t".join(f"{span_tag.code}: {span_tag.name}" for span_tag in SpanTag if span_tag not in SPAN_TAGS_TO_IGNORE)
        yolo_path = "app/data/yolo.yaml"
        # --- 8. Finální data.yaml pro YOLO ---
        yolo_yaml = f"""train: /content/data/train\nval: /content/data/validation\nnc: {len(SpanTag) - len(SPAN_TAGS_TO_IGNORE)}\nname:\n\t{class_names}"""
        with open(yolo_path, "w", encoding="utf-8") as f:
            f.write(yolo_yaml)
        
        print(f" - YOLO: {yolo_path}")

        return True
