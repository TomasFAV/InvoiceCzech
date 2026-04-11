from dataclasses import dataclass
from typing import Any

from common.data.enumerates.CompanyType import CompanyType
from common.data.enumerates.CountryCode import CountryCode
from invoices_generator.utility.json_serializable import json_serializable


@dataclass
class Company(json_serializable):

    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################


    name: str = ""
    street:str = ""
    zip:str = ""
    city:str = ""

    #kraviny navíc
    phone: str = ''
    mail: str = ''
    

    #IČ
    register_id: str = ''
    #DIČ
    tax_id: str = ''

    type: CompanyType = CompanyType.INDIVIDUAL
    country: CountryCode = CountryCode.CZ

    @property
    def address(self)->str:
        return f"{self.street}, {self.zip}, {self.city}"

    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################

    def to_json_donut(self) -> Any:
        return self.__dict__
    
    def to_json_layoutlmv3(self):
        return self.__dict__
