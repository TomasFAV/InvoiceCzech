from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice

class invoice_component(ABC):
    


    def __init__(self):
        pass


    @abstractmethod
    def draw(inv:DInvoice, d:ImageDraw, x:int, y:int, **kwargs)->int:
        """vykreslí komponentu, přičemž bod [offset_x, offset_y] je počátkem soustavy souřadnic,
           vrací y-ovou souřadnici, kde vykreslení skončilo"""
        pass
    

