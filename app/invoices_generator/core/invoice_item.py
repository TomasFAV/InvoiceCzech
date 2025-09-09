#typování abstraktní třída
from dataclasses import dataclass
from typing import Any

from app.invoices_generator.utility.json_serializable import json_serializable


@dataclass
class invoice_item(json_serializable):

    """
    Reprezentace jedné položky na faktuře.

    :param description: Textový popis položky (např. "Notebook XZ715")
    :param quantity: Množství jednotek (např. 2 ks)
    :param ppu: Cena za jednotku bez DPH (Price Per Unit)
    :param price_without_vat: Celková cena bez DPH (ppu * quantity)
    :param vat_percentage: Daň v procentech (např. 21.0 pro 21 %)
    :param vat: Absolutní částka DPH (price_without_vat * vat_percentage / 100)
    :param price_with_vat: Celková cena s DPH (ppu * quantity * (1 + vat_percentage/100))
    """

    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################

    description: str
    quantity: int
    
    #price per unit bez daně
    ppu:float
    
    #celková cena bez daně... ppu*quantity
    price_without_vat: float
    #procentuální daň
    vat_percentage: float
    #absolutní celková daň
    vat:float
    #celková cena s daní...ppu*quantity*(1+vat_percentage)
    price_with_vat:float

    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################

    def to_json_donut(self) -> Any:
        return self.__dict__
    
    def to_json_layoutlmv2(self):
        return self.__dict__