from dataclasses import dataclass, field
from typing import List, Optional

from invoices_generator.core.Bank import Bank
from invoices_generator.core.Company import Company
from invoices_generator.core.enumerates.CurrencyCode import CurrencyCode
from invoices_generator.core.InvoiceItem import InvoiceItem
from invoices_generator.core.VatItem import VatItem
from invoices_generator.utility.json_serializable import json_serializable

from invoices_generator.utility.utils import fmt, fmt_money


@dataclass
class InvoiceData(json_serializable):
    
    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################
    invoice_number: Optional[str] = ""
    variable_symbol: Optional[str] = ""
    bank_account_number: Optional[str] = ""
    IBAN:Optional[str] = ""
    const_symbol: Optional[str] = ""

    # datum vystavení
    issue_date: Optional[str] = ""
    # datum uskutečnění zdanitelného plnění
    taxable_supply_date: Optional[str] = ""
    # datum splatnosti
    due_date: Optional[str] = ""

    supplier: Optional[Company] = field(default_factory=Company)
    customer: Optional[Company] = field(default_factory=Company)

    total_price: Optional[float] = 0.0 #s daní

    bank_account: Optional[Bank] = field(default_factory=Bank)
    payment_type: Optional[str] = ""
    currency: Optional[CurrencyCode] = CurrencyCode.CZK
    

    description: Optional[str] = ""
    items: Optional[List[InvoiceItem]] = field(default_factory=list)


    @property
    def vat(self) -> List[VatItem]:

        vats: List[VatItem] = list()

        for item in self.items:
            found = False

            for vat in vats:
                if (item.vat_percentage == vat.vat_percentage):
                    vat.vat_base += item.price_without_vat
                    vat.vat += item.vat
                    found = True

                    break

            if not found:
                vat = VatItem(item.vat_percentage, item.price_without_vat, item.vat)
                vats.append(vat)

        for vat in vats:
            vat.vat = str(vat.vat)
            vat.vat_base = str(vat.vat_base)
            vat.vat_percentage = str(vat.vat_percentage)

        return vats

    @property
    def calculated_total_price(self) -> float:
        price:float = 0
        for item in self.items:
            price += item.price_with_vat
        return round(price,2)

    @property
    def calculated_total_vat(self) -> float:
        vat:float = 0
        for item in self.items:
            vat += item.vat
        return round(vat,2)

    @property
    def calculated_total_price_without_vat(self) -> float:
        return round(self.calculated_total_price - self.calculated_total_vat,2)
        
    #---------------------------METODY PŘEVODU MEZI STRUKTURAMI--------------------------

    def from_dict(self, data:dict[str, str]):
        self.invoice_number = data.get("invoice_number", self.invoice_number)
        self.variable_symbol = data.get("variable_symbol", self.variable_symbol)
    
        self.const_symbol = data.get("const_symbol", self.const_symbol)
        self.issue_date = data.get("issue_date", self.issue_date)
        self.taxable_supply_date = data.get("taxable_supply_date", self.taxable_supply_date)
        self.due_date = data.get("due_date", self.due_date)
        self.total_price = data.get("total", self.total_price)
        self.IBAN = data.get("iban", self.IBAN)
        
        self.bank_account.BIC = data.get("bic", self.bank_account.BIC)

        self.supplier.register_id = data.get("supp_register_id", self.supplier.register_id)
        self.supplier.tax_id = data.get("supp_tax_id", self.supplier.tax_id)

        self.customer.register_id = data.get("cust_register_id", self.customer.register_id)
        self.customer.tax_id = data.get("cust_tax_id", self.customer.tax_id)

        self.payment_type = data.get("payment_type", self.payment_type)
        self.bank_account_number = data.get("bank_account_number", self.bank_account_number)

    def to_dict(self)->dict[str,str]:
        data:dict[str,str] = dict()
        
        data["invoice_number"] = fmt(str(self.invoice_number))
        
        data["supp_register_id"] = fmt(str(self.supplier.register_id))
        data["supp_tax_id"] = fmt(str(self.supplier.tax_id))

        data["cust_register_id"] = fmt(str(self.customer.register_id)) 
        data["cust_tax_id"] = fmt(str(self.customer.tax_id))

        data["issue_date"] = fmt(str(self.issue_date))
        data["taxable_supply_date"] = fmt(str(self.taxable_supply_date))
        data["due_date"] = fmt(str(self.due_date))

        data["payment_type"] = str(self.payment_type)
        data["bank_account_number"] = fmt(str(self.bank_account_number))

        data["iban"] = fmt(str(self.IBAN))
        data["bic"] = fmt(str(self.bank_account.BIC))

        data["variable_symbol"] = fmt(str(self.variable_symbol))
        data["const_symbol"] = fmt(str(self.const_symbol))
        
        data["total"] = fmt_money(self.total_price, False).replace('.',',')          

        return data