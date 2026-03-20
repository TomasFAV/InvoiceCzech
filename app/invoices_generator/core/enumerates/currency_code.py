from enum import Enum
from typing import Any
from invoices_generator.utility.json_serializable import json_serializable


class currency_code(json_serializable, Enum):
    USD = 'USD'
    EUR = 'EUR'
    CZK = 'Kč'

    def to_json_donut(self)->Any:
        return self.value
    
    def to_json_layoutlmv3(self)->Any:
        return self.value
