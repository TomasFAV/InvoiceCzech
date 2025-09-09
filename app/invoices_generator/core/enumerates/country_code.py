from enum import Enum
from typing import Any

from app.invoices_generator.utility.json_serializable import json_serializable


class country_code(json_serializable, Enum):
    
    CZ = 'CZ'
    EN = 'EN'
    FR = 'FR'
    PL = 'PL'
    GB = 'GB'
    SK = 'SK'
    JP = 'JP'
    DE = 'DE'
    RU = 'RU'

    def to_json_donut(self)->Any:
        return self.value
    
    def to_json_layoutlmv2(self)->Any:
        return self.value