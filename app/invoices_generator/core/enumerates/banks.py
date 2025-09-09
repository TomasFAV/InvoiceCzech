from enum import Enum
from typing import Any

from app.invoices_generator.core.bank import bank
from app.invoices_generator.utility.json_serializable import json_serializable


class banks(json_serializable, Enum):
    CSOB   = bank("ČSOB, a.s.", "0300", "CEKOCZPP")
    KB     = bank("Komerční banka, a.s.", "0100", "KOMBCZPP")
    RB     = bank("Raiffeisenbank, a.s.", "5500", "RZBCCZPP")
    MONETA = bank("MONETA Money Bank, a.s.", "0600", "AGBACZPP")
    FIO    = bank("Fio banka, a.s.", "2010", "FIOBCZPP")
    AIRBANK= bank("Air Bank, a.s.", "3030", "AIRACZPP")
    CS     = bank("Česká spořitelna, a.s.", "0800", "GIBACZPX")

    def to_json_donut(self) -> Any:
        return self.value.__dict__
    
    def to_json_layoutlmv2(self):
        return self.value.__dict__