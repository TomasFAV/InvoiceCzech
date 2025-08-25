from enum import Enum
from typing import Any

from app.invoices.core.bank import bank
from app.invoices.utility.json_serializable import json_serializable


class banks(json_serializable, Enum):
    CSOB   = bank("Československá obchodní banka, a.s.", "0300", "CEKOCZPP")
    KB     = bank("Komerční banka, a.s.", "0100", "KOMBCZPP")
    RB     = bank("Raiffeisenbank, a.s.", "5500", "RZBCCZPP")
    MONETA = bank("MONETA Money Bank, a.s.", "0600", "AGBACZPP")
    FIO    = bank("Fio banka, a.s.", "2010", "FIOBCZPP")
    AIRBANK= bank("Air Bank, a.s.", "3030", "AIRACZPP")
    CS     = bank("Česká spořitelna, a.s.", "0800", "GIBACZPX")

    def to_json(self) -> Any:
        return self.value.__dict__