from enum import Enum
from invoices_generator.core.enumerates.token_tags import token_tags

class span_tags(Enum):
    O = (0,"o", token_tags.O)
    INVOICE_NUMBER = (1,"invoice_number", token_tags.B_INVOICE_NUMBER)
    SUPPLIER_REGISTER_ID = (2,"supp_register_id", token_tags.B_SUPPLIER_REGISTER_ID)
    SUPPLIER_TAX_ID = (3,"supp_tax_id", token_tags.B_SUPPLIER_TAX_ID)
    CUSTOMER_REGISTER_ID = (4,"cust_register_id", token_tags.B_CUSTOMER_REGISTER_ID)
    CUSTOMER_TAX_ID = (5,"cust_tax_id", token_tags.B_CUSTOMER_TAX_ID)
    ISSUE_DATE = (6,"issue_date", token_tags.B_ISSUE_DATE)
    TAXABLE_SUPPLY_DATE = (7,"taxable_supply_date", token_tags.B_TAXABLE_SUPPLY_DATE)
    DUE_DATE = (8,"due_date", token_tags.B_DUE_DATE)
    PAYMENT_TYPE = (9,"payment_type", token_tags.B_PAYMENT_TYPE)
    BANK_ACCOUNT_NUMBER = (10,"bank_account_number", token_tags.B_BANK_ACCOUNT_NUMBER)
    IBAN = (11,"iban", token_tags.B_IBAN)
    BIC = (12,"bic", token_tags.B_BIC)
    VARIABLE_SYMBOL = (13,"variable_symbol", token_tags.B_VARIABLE_SYMBOL)
    CONST_SYMBOL = (14,"const_symbol", token_tags.B_CONST_SYMBOL)
    TOTAL = (15,"total", token_tags.B_TOTAL)

    #do budoucna v pripade rozsireni prace
    VAT_PERCENTAGE = (16,"vat_percentage", token_tags.B_VAT_PERCENTAGE)
    VAT_BASE = (17,"vat_base", token_tags.B_VAT_BASE)
    VAT = (18,"vat", token_tags.B_VAT)
    

    def __init__(self, code:int, text:str, ref:token_tags):
        super().__init__()

        self.code = code
        self.text = text
        self.ref = ref

    @classmethod
    def from_id(cls, tag_id):
        for tag in cls:
            if tag.value[0] == tag_id:
                return tag
        return cls.O  # Nebo None, pokud ID neexistuje
    
    @classmethod
    def from__token_id(cls, tag_id):
        if tag_id == 0:
            return cls.O
        
        # Pokud je tag_id sudé (I-tag), převedeme ho na liché (B-tag)
        # B-tagy jsou: 1, 3, 5... | I-tagy jsou: 2, 4, 6...
        base_id = tag_id if tag_id % 2 != 0 else tag_id - 1
        
        for tag in cls:
            # tag.value[2] je token_tags objekt, který má atribut .code
            if tag.value[2].code == base_id:
                return tag
                
        return cls.O

SPAN_TAGS_TO_IGNORE = [span_tags.VAT, span_tags.VAT_BASE, span_tags.VAT_PERCENTAGE]