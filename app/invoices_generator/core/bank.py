from dataclasses import dataclass
from typing import Any
from invoices_generator.utility.json_serializable import json_serializable


@dataclass
class bank(json_serializable):

    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################
    
    name: str = ""
    code: str = ""
    BIC: str = ""


    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################

    def to_json_donut(self) -> Any:
        return self.__dict__
    
    def to_json_layoutlmv3(self):
        return self.__dict__
