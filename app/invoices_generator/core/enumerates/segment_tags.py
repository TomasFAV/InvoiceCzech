from enum import Enum

class segment_tags(Enum):
    O = (0,"o")
    SUPPLIER_BLOCK = (1,"supp_block")
    SUPPLIER_INNER_BLOCK = (2, "supp_inner_block")
    CUSTOMER_BLOCK = (3,"cust_block")
    CUSTOMER_INNER_BLOCK = (4,"cust_inner_block")
    ITEMS_BLOCK = (5,"items_block")
    VAT_BLOCK = (6, "vat_block")    

    def __init__(self, code:int, text:str):
        super().__init__()

        self.code = code
        self.text = text

    @classmethod
    def from_id(cls, tag_id):
        for tag in cls:
            if tag.code == tag_id:
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
