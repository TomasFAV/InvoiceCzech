from abc import ABC, abstractmethod
from typing import Any

class json_serializable:

    @abstractmethod
    def to_json(self)->str:
        """
        Vrátí instanci ve formě json, nemění obsah jednotlivých instancí
        """
        pass