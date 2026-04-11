from pathlib import Path
from typing import Any

from PIL import Image
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.processors.IEProcessors.DonutIEProcessor import DonutIEConfig
from common.invoice.processors.InvoiceExporter import InvoiceExporter
from common.invoice.processors.InvoiceImporter import InvoiceImporter
from common.invoice.models.GToken import GToken
from common.invoice.models.GSegment import GSegment
from common.invoice.models.GSpan import GSpan
from common.utils.consts import DEFAULT_SEGMENT_COLOR, DEFAULT_TOKEN_COLOR
from common.enumerates.SegmentTag import SegmentTag
from common.enumerates.TokenTag import TokenTag
from common.invoice.OperationResult import OperationResult
from common.Session import Session


class Controller:

    def __init__(self, session:Session):
        self._invoice_importer:InvoiceImporter = InvoiceImporter()
        self._invoice_exporter:InvoiceExporter = InvoiceExporter()

        self.session: Session = session

    #--------------veřejné api do session ----------------------

    def get_tokens(self)->OperationResult:
        return OperationResult(True, self.session.invoice._tokens)
    
    def get_spans(self)->OperationResult:
        return OperationResult(True, self.session.invoice._spans)
    
    def get_segments(self)->OperationResult:
        return OperationResult(True, self.session.invoice._segments)
    


    def get_selected_tokens(self) -> OperationResult:
        return OperationResult(True, self.session.selected_tokens)
    
    def get_selected_spans(self) -> OperationResult:
        return OperationResult(True, self.session.selected_spans)
    
    def get_selected_segments(self) -> OperationResult:
        return OperationResult(True, self.session.selected_segments)
    


    def get_token_by_id(self, id:int) ->OperationResult:
        return OperationResult(True, self.session.invoice.get_token_by_id(id))
    
    def get_span_by_id(self, id:int) ->OperationResult:
        return OperationResult(True, self.session.invoice.get_span_by_id(id))
    
    def get_segment_by_id(self, id:int) ->OperationResult:
        return OperationResult(True, self.session.invoice.get_segment_by_id(id))
    


    def create_token(self, bbox: tuple[float, float, float, float], text: str) -> OperationResult:
        token = GToken(None,text,bbox,TokenTag.O,DEFAULT_TOKEN_COLOR,synthetic=True)
        return OperationResult(self.append_token(token))

    def create_segment(self, bbox: tuple[float, float, float, float]) -> OperationResult:
        segment = GSegment(None, bbox,SegmentTag.O, DEFAULT_SEGMENT_COLOR)
        return OperationResult(self.append_segment(segment))
    


    def append_token(self, tok: GToken) ->OperationResult:
        return OperationResult(self.session.invoice.append_token(tok))
    
    def append_span(self, span: GSpan) ->OperationResult:
        return OperationResult(self.session.invoice.append_span(span))
    
    def append_segment(self, segment:GSegment) -> OperationResult:
        return OperationResult(self.session.invoice.append_segment(segment))
    


    def remove_token(self, token:GToken) -> OperationResult:
        if token in self.session.selected_spans:
            self.session.selected_tokens.remove(token)

        return OperationResult(self.session.invoice.remove_token(token)) 

    def remove_span(self, span:GSpan) -> OperationResult:
        if span in self.session.selected_spans:
            self.session.selected_spans.remove(span)

        return OperationResult(self.session.invoice.remove_span(span)) 

    def remove_segment(self, segment:GSegment) -> OperationResult:
        if segment in self.session.selected_segments:
            self.session.selected_segments.remove(segment)

        return OperationResult(self.session.invoice.remove_segment(segment)) 



    def reset_token(self, token:GToken) -> OperationResult:
        return OperationResult(self.session.invoice.reset_token(token)) 

    def reset_token_tags(self, *kwargs) -> OperationResult:
        return OperationResult(self.session.invoice.reset_tokens())    


    def is_in_spans(self, tok: GToken) -> OperationResult:
        return OperationResult(True, self.session.invoice.is_in_spans(tok))
    

    
    def get_invoice_dict_from_spans(self)->dict[str, Any]:
        """Ze spanů"""
        return self._invoice_exporter.export_donut(self.session.invoice, None, DonutIEConfig.FROM_SPANS)
    
    def get_invoice_dict(self)->dict[str, Any]:
        """Z json informací"""
        return self.session.invoice_data.to_dict()
    


    
    def get_invoice_image(self)->Image.Image|None:
        if self.session.invoice.image:
            return self.session.invoice.image

        if self.session.image_path:
            self.session.invoice.load_image(self.session.image_path)
            return self.session.invoice.image

        return None 





    def invoice_from_layoutlmv3(self, invoice:Invoice, layoutlmv3_path:Path, file_path:Path)-> bool:
        return self._invoice_importer.import_layoutlmv3(invoice, layoutlmv3_path, file_path)
    
    def invoice_data_from_donut(self, invoice_data:InvoiceData, donut_path, file_path) -> bool:
        return self._invoice_importer.import_donut(invoice_data, donut_path, file_path)