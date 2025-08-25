from dataclasses import dataclass
from datetime import date, timedelta
import json
import random
import re
from typing import Type

from app.invoices.core.bank import bank
from app.invoices.core.company import company
from app.invoices.core.enumerates.banks import banks
from app.invoices.core.enumerates.company_type import company_type
from app.invoices.core.enumerates.country_code import country_code
from app.invoices.core.enumerates.currency_code import currency_code
from app.invoices.core.enumerates.payment_type import payment_type
from app.invoices.core.invoice import invoice
from app.invoices.core.invoice_item import invoice_item
from app.invoices.templates.alza_invoice import alza_invoice
from app.invoices.templates.general_invoice import general_invoice
from app.invoices.templates.phone_invoice import phone_invoice
from app.invoices.templates.post_invoice import post_invoice
from app.invoices.templates.restaurant_receipt import restaurant_receipt
from app.invoices.templates.store_receipt import store_receipt
from app.invoices.templates.classic_invoice import classic_invoice
from app.invoices.templates.modern_invoice import modern_invoice
from app.invoices.templates.colorful_invoice import colorful_invoice
from app.invoices.templates.compact_invoice import compact_invoice
from app.invoices.templates.a_invoice import a_invoice
from app.invoices.templates.simple_invoice import simple_invoice
from app.invoices.templates.inverted_invoice import inverted_invoice
from app.invoices.templates.random_invoice import random_invoice

from app.invoices.utility.invoice_consts import *


@dataclass
class invoice_generator:
    
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

    def __generate_company(self)->company:

        is_company:bool = True if random.randrange(0, 4) > 1 else False

        company_name:str
        street_name:str = street_names[random.randrange(0, len(street_names))]
        zip_code:str = f"{random.randint(0, 99999):05d}" #peticiferne cislo
        city_name:str = city_names[random.randrange(0, len(city_names))]
        phone:str = "+420" if random.randrange(0,1) == 1 else ("") + f"{random.randint(000000000, 999999999):09d}"
        register_id:str
        tax_id:str
        type:company_type

        if(is_company):

            company_name = company_names[random.randrange(0, len(company_names))]
            register_id = f"{random.randint(00000000, 99999999):08d}" #osmimistne cislo
            tax_id = "" if random.randrange(0,1) == 1 else (f"CZ{register_id}")
            type = company_types[random.randrange(0, len(company_types))]
        
        else: 
            
            company_name = person_names[random.randrange(0, len(person_names))]
            register_id = "" if random.randrange(0, 4) > 1 else f"{random.randint(00000000, 99999999):08d}" #osmimistne cislo
            tax_id = ""
            type = company_type.INDIVIDUAL

        return company(name=company_name,
                        street=street_name,
                        zip=zip_code,
                        city=city_name,
                        phone=phone,
                        register_id=register_id,
                        tax_id=tax_id,
                        type=type)
    
    def __generate_bank_account(self, bank:bank) -> tuple[str, str]:
        # základní číslo účtu (1–10 číslic), doplním na 10
        account_number = f"{random.randint(1, 9999999999):010d}"

        # předčíslí (nepovinné), tady dám třeba náhodně 0–6 číslic
        prefix = f"{random.randint(0, 999999):06d}"

        number = f"{prefix}-{account_number}/{bank.code}"

        # vytvoření IBANu (CZ + 2 číslice + kód banky + číslo účtu)
        check_digits = f"{random.randint(10, 99)}"
        iban = f"CZ{check_digits}{bank.code}{account_number:0>16}"  # vždy 24 znaků
        
        return (number, iban)

    def __generate_item(self)->invoice_item:
        quantity:int = random.randrange(1, 40)
        ppu = random.randrange(100, 99999)

        price_without_vat = ppu*quantity
        vat_percentage = vat_percentages[random.randrange(0, len(vat_percentages))]

        vat = price_without_vat * (vat_percentage/100)
        price_with_vat = price_without_vat + vat
        name = item_names[random.randrange(0, len(item_names))]

        return invoice_item(description=name, quantity=quantity, ppu=ppu,
                            price_without_vat=price_without_vat, vat=vat,
                            vat_percentage=vat_percentage, price_with_vat=price_with_vat)


    def __generate_items(self)->tuple[list[invoice_item], float, float]:
        items:list[invoice_item] = list()
        quantity = random.randrange(1,7)
        total_price:float = 0
        total_vat:float = 0


        for _ in range(quantity):
            item = self.__generate_item()
            items.append(item)

            total_price += item.price_with_vat
            total_vat += item.vat

        return (items, total_price, total_vat)

    def __generate_invoice_number(self) -> str:
        return f"{random.randrange(1980, 2100)}-{random.randrange(0,999999)}"
    
    def __generate_variable_symbol(self, invoice_number:str)->str:
        ran = random.randrange(0,4)

        if(ran>1):
            return re.sub(r"\D", "", str(invoice_number))
        else:
            return str(random.randrange(0,999999))

    def __generate_const_symbol(self)->str:
        ran = random.randrange(0,4)

        if(ran>1):
            return ""
        else:
            return f"{random.randrange(0, 9999):04d}"
    
    def __generate_invoice_dates(self) -> tuple[str, str, str]:
        today = date.today()
        
        # náhodné datum vystavení během posledních X dní
        random_offset = random.randint(0, 1440)
        issue_date_obj = today - timedelta(days=random_offset)

        def fmt(d: date) -> str:
            return d.strftime("%d.%m.%Y")  # evropský formát

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

    def __generate_folder(self, folder: str, count: int) -> None:
        for _ in range(count):
            supp = self.__generate_company()
            cust = self.__generate_company()

            bank = banks_[random.randrange(0, len(banks_))]
            payment = payments[random.randrange(0, len(payments))]

            items, total_price, total_vat = self.__generate_items()

            invoice_number = self.__generate_invoice_number()
            variable_symbol = self.__generate_variable_symbol(invoice_number)
            const_symbol = self.__generate_const_symbol()

            bank_account_number, IBAN = self.__generate_bank_account(bank)

            issue_date, taxable_supply_date, due_date = self.__generate_invoice_dates()

            invoice_classes: list[type[invoice]] = [
                alza_invoice,
                general_invoice,
                phone_invoice,
                post_invoice,
                restaurant_receipt,
                store_receipt,
                classic_invoice,
                modern_invoice,
                colorful_invoice, 
                compact_invoice,
                a_invoice,
                simple_invoice,
                inverted_invoice,
                random_invoice,
                random_invoice,
                random_invoice,
                random_invoice,
                random_invoice,
            ]

            cls = random.choice(invoice_classes)

            instance = cls(
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
                rounding=0,
                total_vat=total_vat,
                total_price=total_price,
                bank_account=bank,
                payment=payment,
                items=items,
            )

            img_path = f"app/data/{folder}/{cls.__name__}_{invoice_number}.png"
            meta_path = f"app/data/{folder}/metadata.jsonl"

            if instance.generate_img(img_path):
                print(f"{cls.__name__}: faktura byla vytvořena ({folder}).")

            with open(meta_path, "a", encoding="utf-8") as f:
                output = {
                    "file_name": f"{cls.__name__}_{invoice_number}.png",
                    "ground_truth": {
                        "gt_parse": instance.to_json()
                    }
                }
                f.write(json.dumps(output, ensure_ascii=False) + "\n")

                
    def generate(self, train_count:int, test_count:int, validation_count:int)->bool:
        
        if(train_count>0):
            self.__generate_folder("train", train_count)

        if(test_count>0):
            self.__generate_folder("test", test_count)

        if(validation_count>0):
            self.__generate_folder("validation", validation_count)

        return True
    

    pass
