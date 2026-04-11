from pathlib import Path
from common.invoice.processors.IEProcessors.DonutIEProcessor import DonutIEProcessor
from common.invoice.processors.IEProcessors.LayoutLMV3IEProcessor import LayoutLMV3IEProcessor
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData


class InvoiceImporter:
    def __init__(self):
        self.__donut_ie_processor: DonutIEProcessor = DonutIEProcessor()
        self.__layoutlmv3_ie_processor: LayoutLMV3IEProcessor = LayoutLMV3IEProcessor()

    def import_donut(self, invoice_data:InvoiceData, donut_file_path: Path, invoice_file_path:Path):
        """
            Načte json data(dict) do invoice_data
        """
        return self.__donut_ie_processor._import(invoice_data, donut_file_path, invoice_file_path)
        ...

    def import_layoutlmv3(self, invoice:Invoice, layoutlmv3_file_path: Path, invoice_file_path:Path) -> bool:
        """
            Načte fakturu do proměnné invoice
        """
        return self.__layoutlmv3_ie_processor._import(invoice, layoutlmv3_file_path, invoice_file_path)