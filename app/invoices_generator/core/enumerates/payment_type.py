from enum import Enum
from typing import Any
from app.invoices_generator.utility.json_serializable import json_serializable


class payment_type(json_serializable, Enum):
    CASH = "hotově"
    CARD = "kartou"
    BANK_TRANSFER = "bankovní převod"
    ONLINE = "online platba"

    def to_json_donut(self)->Any:
        return self.value
    
    def to_json_layoutlmv2(self)->Any:
        return self.value