from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.Processors.IEProcessors.LayoutLMV3IEProcessor import LayoutLMV3IEConfig, LayoutLMV3IEProcessor
from common.invoice.Processors.IEProcessors.CocoIEProcessor import CocoIEProcessor
from common.invoice.Processors.IEProcessors.DonutIEProcessor import DonutIEConfig, DonutIEProcessor
from common.invoice.Processors.IEProcessors.YoloIEProcessor import YoloIEProcessor


class InvoiceExporter:

    def __init__(self):
        self.__donut_ie_processor: DonutIEProcessor = DonutIEProcessor()
        self.__layoutlmv3_ie_processor: LayoutLMV3IEProcessor = LayoutLMV3IEProcessor()
        self.__coco_ie_processor: CocoIEProcessor = CocoIEProcessor()
        self.__yolo_ie_processor: YoloIEProcessor = YoloIEProcessor()

    def export_donut(self, invoice:Invoice|None = None, original_data:InvoiceData|None = None, option: DonutIEConfig = DonutIEConfig.FROM_SPANS):
        return self.__donut_ie_processor._export(invoice, original_data, option)

    def export_layoutlmv3(self, invoice:Invoice, option: LayoutLMV3IEConfig = LayoutLMV3IEConfig.WITH_TESSERACT):
        return self.__layoutlmv3_ie_processor._export(invoice, option)

    def export_coco(self, invoice: Invoice, path_to_metadata:str, invoice_file_path:str):
        return self.__coco_ie_processor._export(invoice, path_to_metadata, invoice_file_path)
    
    def export_yolo(self, invoice:Invoice):
        return self.__yolo_ie_processor._export(invoice)