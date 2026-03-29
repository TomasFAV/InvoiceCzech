from abc import ABC, abstractmethod
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Renderers.TextRenderer import TextRenderer

class InvoiceTemplate(ABC):


    @staticmethod
    @abstractmethod
    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        ...