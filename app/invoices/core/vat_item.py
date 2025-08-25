#typování abstraktní třída
from dataclasses import dataclass
from typing import Any
from app.invoices.utility.json_serializable import json_serializable


@dataclass
class vat_item(json_serializable):
    """
    Reprezentace jedné daňové položky na faktuře.

    :param vat_percentage: Procentuální sazba DPH (např. 21.0 pro 21 %)
    :param vat_base: Základ daně – částka bez DPH, ze které se daň počítá
    :param vat: Absolutní částka DPH v měně (vat_base * vat_percentage / 100)
    """


    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################

    #procenta_daně
    vat_percentage: float
    #základ daně
    vat_base: float
    #daň v měně
    vat: float

    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################

    def to_json(self)->Any:
        return self.__dict__