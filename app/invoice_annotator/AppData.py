from dataclasses import dataclass

from invoice_annotator.enumerates.ContextMenuOptions import ContextMenuOptions
from invoice_annotator.model.GInvoice import GInvoice
from invoice_annotator.utils.GToken import GToken


class AppData:

    """Slouží pro statické uchovávání a držení proměnných napříč aplikací"""
    invoice: GInvoice = GInvoice()

    @staticmethod
    def reset() -> None:
        AppData.invoice = GInvoice()
