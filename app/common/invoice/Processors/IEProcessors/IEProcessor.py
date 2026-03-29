from abc import ABC, abstractmethod
from typing import Any

from common.invoice.Processors.InvoiceOCRAligner import InvoiceOCRAligner


class IEProcessor(ABC):

    def __init__(self):
        self.invoice_ocr_aligner: InvoiceOCRAligner = InvoiceOCRAligner()

    @abstractmethod
    def _import(self)->bool:
        ...

    @abstractmethod
    def _export(self)->dict[str, Any]:
        ...