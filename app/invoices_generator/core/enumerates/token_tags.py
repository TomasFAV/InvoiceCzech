from enum import Enum
from typing import Any

from app.invoices_generator.utility.json_serializable import json_serializable


class token_tags(Enum):
    O = (0,"o", "O")
    
    B_INVOICE_NUMBER = (1,"b_invoice_number", "I_INVOICE_NUMBER")
    I_INVOICE_NUMBER = (2,"i_invoice_number", "I_INVOICE_NUMBER")

    B_SUPPLIER_REGISTER_ID = (3,"b_supp_register_id", "I_SUPPLIER_REGISTER_ID")
    I_SUPPLIER_REGISTER_ID = (4,"i_supp_register_id", "I_SUPPLIER_REGISTER_ID")
    
    B_SUPPLIER_TAX_ID = (5,"b_supp_tax_id", "I_SUPPLIER_TAX_ID")
    I_SUPPLIER_TAX_ID = (6,"i_supp_tax_id", "I_SUPPLIER_TAX_ID")
    
    B_CUSTOMER_REGISTER_ID = (7,"b_cust_register_id", "I_CUSTOMER_REGISTER_ID")
    I_CUSTOMER_REGISTER_ID = (8,"i_cust_register_id", "I_CUSTOMER_REGISTER_ID")
    
    B_CUSTOMER_TAX_ID = (9,"b_cust_tax_id", "I_CUSTOMER_TAX_ID")
    I_CUSTOMER_TAX_ID = (10,"i_cust_tax_id", "I_CUSTOMER_TAX_ID") 
    
    B_ISSUE_DATE = (11,"b_issue_date", "I_ISSUE_DATE")
    I_ISSUE_DATE = (12,"i_issue_date", "I_ISSUE_DATE")
    
    B_TAXABLE_SUPPLY_DATE = (13,"b_taxable_supply_date", "I_TAXABLE_SUPPLY_DATE")
    I_TAXABLE_SUPPLY_DATE = (14,"i_taxable_supply_date", "I_TAXABLE_SUPPLY_DATE")
    
    B_DUE_DATE = (15,"b_due_date", "I_DUE_DATE")
    I_DUE_DATE = (16,"i_due_date", "I_DUE_DATE")
    
    B_PAYMENT_TYPE = (17,"b_payment_type", "I_PAYMENT_TYPE")
    I_PAYMENT_TYPE = (18,"i_payment_type", "I_PAYMENT_TYPE")
    
    B_BANK_ACCOUNT_NUMBER = (19,"b_bank_account_number", "I_BANK_ACCOUNT_NUMBER")
    I_BANK_ACCOUNT_NUMBER = (20,"i_bank_account_number", "I_BANK_ACCOUNT_NUMBER")
    
    B_IBAN = (21,"b_iban", "I_IBAN")
    I_IBAN = (22,"i_iban", "I_IBAN")
    
    B_BIC = (23,"b_bic", "I_BIC")
    I_BIC = (24,"i_bic", "I_BIC")
    
    B_VARIABLE_SYMBOL = (25,"b_variable_symbol", "I_VARIABLE_SYMBOL")
    I_VARIABLE_SYMBOL = (26,"i_variable_symbol", "I_VARIABLE_SYMBOL")
    
    B_CONST_SYMBOL = (27,"b_const_symbol", "I_CONST_SYMBOL")
    I_CONST_SYMBOL = (28,"i_const_symbol", "I_CONST_SYMBOL")
    
    B_VAT_PERCENTAGE = (29,"b_vat_percentage", "I_VAT_PERCENTAGE")
    I_VAT_PERCENTAGE = (30,"i_vat_percentage", "I_VAT_PERCENTAGE")
    
    B_VAT_BASE = (31,"b_vat_base", "I_VAT_BASE")
    I_VAT_BASE = (32,"i_vat_base", "I_VAT_BASE")
    
    B_VAT = (33,"b_vat", "I_VAT")
    I_VAT = (34,"i_vat", "I_VAT")
    
    B_TOTAL = (35,"b_total", "I_TOTAL")
    I_TOTAL = (36,"i_total", "I_TOTAL")


    def __init__(self, code:int, text:str, ref:str):
        super().__init__()

        self.code = code
        self.text = text
        self._ref = ref

    @property
    def ref(self)->Any:
        return token_tags[self._ref] if isinstance(self._ref, str) else self._ref