from enum import Enum
from typing import Any

from app.invoices.utility.json_serializable import json_serializable


class company_type(json_serializable, Enum):
    SRO = 's.r.o'
    AS = 'a.s.'
    SP = 's.p.'
    INDIVIDUAL = ''

    def to_json(self)->Any:
        return self.value