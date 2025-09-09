from enum import Enum
from typing import Any

from app.invoices_generator.core.enumerates.span_tags import span_tags


class relationship_types(Enum):
    NONE = (0,"None", span_tags.O, span_tags.O)
    BASE_OF = (1,"base_of", span_tags.VAT_BASE, span_tags.VAT_PERCENTAGE)
    VAT_OF = (2,"vat_of", span_tags.VAT, span_tags.VAT_PERCENTAGE)

    def __init__(self, code:int, text:str, span_type_a:span_tags, span_type_b:span_tags):
        super().__init__()

        self.code = code
        self.text = text

        self.span_type_a = span_type_a
        self.span_type_b = span_type_b

    @classmethod
    def get_relationship_id(self, span_type_a:span_tags, span_type_b:span_tags)->int:
        for type in list(relationship_types):
            if(type.span_type_a == span_type_a and type.span_type_b == span_type_b):
                return type.code
        
        return -1