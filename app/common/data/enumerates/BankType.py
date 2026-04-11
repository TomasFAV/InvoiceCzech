from enum import Enum
from typing import Any

from common.data.Bank import Bank
from invoices_generator.utility.json_serializable import json_serializable


class BankType(json_serializable, Enum):
    CSOB   = Bank("ČSOB, a.s.", "0300", "CEKOCZPP")
    KB     = Bank("Komerční banka, a.s.", "0100", "KOMBCZPP")
    RB     = Bank("Raiffeisenbank, a.s.", "5500", "RZBCCZPP")
    MONETA = Bank("MONETA Money Bank, a.s.", "0600", "AGBACZPP")
    FIO    = Bank("Fio banka, a.s.", "2010", "FIOBCZPP")
    AIRBANK= Bank("Air Bank, a.s.", "3030", "AIRACZPP")
    CS     = Bank("Česká spořitelna, a.s.", "0800", "GIBACZPX")

    def to_json_donut(self) -> Any:
        return self.value.__dict__
    
    def to_json_layoutlmv3(self):
        return self.value.__dict__
