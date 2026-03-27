from dataclasses import dataclass, field

from anyio import Path
from invoice_annotator.utils.GSegment import GSegment
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
from invoice_annotator.model.GInvoice import GInvoice

@dataclass
class Session:

    """Slouží pro statické uchovávání a držení proměnných napříč aplikací"""
    
    image_path:Path|None = None

    selected_tokens: list[GToken] = field(default_factory=list)
    selected_spans: list[GSpan] = field(default_factory=list)
    selected_segments: list[GSegment] = field(default_factory=list)
    
    invoice: GInvoice = field(default_factory=lambda: GInvoice())

    def reset(self) -> None:
        self.invoice = GInvoice()
        self.image_path = None