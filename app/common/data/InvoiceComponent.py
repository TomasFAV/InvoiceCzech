from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer

class InvoiceComponent(ABC):
    


    def __init__(self):
        pass

    
    @abstractmethod
    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice, x:int, y:int, **kwargs)->int:
        pass

