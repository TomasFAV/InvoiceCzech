from enum import Enum
from typing import Any
from app.invoices.utility.json_serializable import json_serializable


class currency_code(json_serializable, Enum):
    USD = 'USD'
    EUR = 'EUR'
    CZK = 'Kč'

    def to_json(self)->Any:
        return self.value