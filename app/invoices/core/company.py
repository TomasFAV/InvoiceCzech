from dataclasses import dataclass
from typing import Any

from app.invoices.core.enumerates.company_type import company_type
from app.invoices.core.enumerates.country_code import country_code
from app.invoices.utility.json_serializable import json_serializable


@dataclass
class company(json_serializable):

    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################


    name: str
    street:str
    zip:str
    city:str

    phone: str = ''

    #IČ
    register_id: str = ''
    #DIČ
    tax_id: str = ''
    type: company_type = company_type.INDIVIDUAL
    country: country_code = country_code.CZ

    @property
    def address(self)->str:
        return f"{self.street} {self.zip} {self.city}"

    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################

    def to_json(self)->Any:
        return self.__dict__