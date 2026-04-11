from datetime import date, timedelta
import random
import secrets

from common.invoice.models.InvoiceData import InvoiceData
from common.data.Bank import Bank
from common.data.InvoiceItem import InvoiceItem
from common.data.Company import Company
from common.data.invoice_consts import *

class DataGenerator:

    def generate_invoice_data(max_items_quantity:int = 7)->InvoiceData:
        supp = DataGenerator.generate_company()
        cust = DataGenerator.generate_company()
        bank = banks_[random.randrange(0, len(banks_))]
        payment = payments[random.randrange(0, len(payments))]
        items, total_price, total_vat = DataGenerator.generate_items(max_items_quantity)
        invoice_number = DataGenerator.generate_invoice_number()
        variable_symbol = DataGenerator.generate_variable_symbol(invoice_number)
        const_symbol = DataGenerator.generate_const_symbol()
        bank_account_number, IBAN = DataGenerator.generate_bank_account(bank)
        issue_date, taxable_supply_date, due_date = DataGenerator.generate_invoice_dates()

        data = InvoiceData(
                    invoice_number=invoice_number,
                    variable_symbol=variable_symbol,
                    bank_account_number=bank_account_number,
                    IBAN=IBAN,
                    issue_date=issue_date,
                    taxable_supply_date=taxable_supply_date,
                    due_date=due_date,
                    const_symbol=const_symbol,
                    supplier=supp,
                    customer=cust,
                    total_price=total_price,
                    bank_account=bank,
                    payment_type=payment,
                    items=items,
                )
        return data

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