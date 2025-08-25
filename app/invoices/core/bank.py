from dataclasses import dataclass
from typing import Any
from app.invoices.utility.json_serializable import json_serializable


@dataclass
class bank(json_serializable):

    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################
    
    name: str
    code: str
    BIC: str


    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################

    def to_json(self)->Any:
        return self.__dict__