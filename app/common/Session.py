from dataclasses import dataclass, field
from pathlib import Path

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.models.GSegment import GSegment
from common.invoice.models.GSpan import GSpan
from common.invoice.models.GToken import GToken

@dataclass
class Session:

    """Slouží pro statické uchovávání a držení proměnných napříč aplikací"""
    
    image_path:Path|None = None

    selected_tokens: list[GToken] = field(default_factory=list)
    selected_spans: list[GSpan] = field(default_factory=list)
    selected_segments: list[GSegment] = field(default_factory=list)
    
    invoice: Invoice = field(default_factory=lambda: Invoice())
    invoice_data: InvoiceData = field(default_factory=lambda: InvoiceData())

    def reset(self) -> None:
        self.invoice = Invoice()
        self.invoice_data = InvoiceData()

        self.selected_segments = list()
        self.selected_spans = list()
        self.selected_tokens = list()

        self.image_path = None