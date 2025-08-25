from enum import Enum
from typing import Any
from app.invoices.utility.json_serializable import json_serializable


class payment_type(json_serializable, Enum):
    CASH = "hotově"
    CARD = "kartou"
    BANK_TRANSFER = "bankovní převod"
    ONLINE = "online platba"

    def to_json(self)->Any:
        return self.value