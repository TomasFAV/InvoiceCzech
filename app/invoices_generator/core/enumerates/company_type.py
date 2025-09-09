from enum import Enum
from typing import Any

from app.invoices_generator.utility.json_serializable import json_serializable


class company_type(json_serializable, Enum):
    SRO = 's.r.o'
    AS = 'a.s.'
    SP = 's.p.'
    INDIVIDUAL = ''

    def to_json_donut(self)->Any:
        return self.value
    
    def to_json_layoutlmv2(self)->Any:
        return self.value