from enum import Enum
from common.enumerates.TokenTag import TokenTag

class SpanTag(Enum):
    O = (0,"o", TokenTag.O)
    INVOICE_NUMBER = (1,"invoice_number", TokenTag.B_INVOICE_NUMBER)
    SUPPLIER_REGISTER_ID = (2,"supp_register_id", TokenTag.B_SUPPLIER_REGISTER_ID)
    SUPPLIER_TAX_ID = (3,"supp_tax_id", TokenTag.B_SUPPLIER_TAX_ID)
    CUSTOMER_REGISTER_ID = (4,"cust_register_id", TokenTag.B_CUSTOMER_REGISTER_ID)
    CUSTOMER_TAX_ID = (5,"cust_tax_id", TokenTag.B_CUSTOMER_TAX_ID)
    ISSUE_DATE = (6,"issue_date", TokenTag.B_ISSUE_DATE)
    TAXABLE_SUPPLY_DATE = (7,"taxable_supply_date", TokenTag.B_TAXABLE_SUPPLY_DATE)
    DUE_DATE = (8,"due_date", TokenTag.B_DUE_DATE)
    PAYMENT_TYPE = (9,"payment_type", TokenTag.B_PAYMENT_TYPE)
    BANK_ACCOUNT_NUMBER = (10,"bank_account_number", TokenTag.B_BANK_ACCOUNT_NUMBER)
    IBAN = (11,"iban", TokenTag.B_IBAN)
    BIC = (12,"bic", TokenTag.B_BIC)
    VARIABLE_SYMBOL = (13,"variable_symbol", TokenTag.B_VARIABLE_SYMBOL)
    CONST_SYMBOL = (14,"const_symbol", TokenTag.B_CONST_SYMBOL)
    TOTAL = (15,"total", TokenTag.B_TOTAL)

    #do budoucna v pripade rozsireni prace
    #VAT_PERCENTAGE = (16,"vat_percentage", TokenTag.B_VAT_PERCENTAGE)
    #VAT_BASE = (17,"vat_base", TokenTag.B_VAT_BASE)
    #VAT = (18,"vat", TokenTag.B_VAT)
    

    def __init__(self, code:int, text:str, ref:TokenTag):
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

    def __str__(self):
        return self.text

SPAN_TAGS_TO_IGNORE = []