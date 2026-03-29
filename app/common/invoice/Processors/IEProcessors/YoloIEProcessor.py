from typing import Any
from common.enumerates.SpanTag import SPAN_TAGS_TO_IGNORE
from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX
from common.invoice.models.Invoice import Invoice
from common.invoice.OperationResult import OperationResult
from common.invoice.Processors.IEProcessors.IEProcessor import IEProcessor

class YoloIEProcessor(IEProcessor):


    def _export(self, invoice:Invoice)->dict[str, Any]:
        result: OperationResult = OperationResult(False)

        result = self.__to_json_yolo(invoice)

        if(not result.ok):
            if isinstance(result.passed_value, str):
                raise result.passed_value
            else:
                raise "Something went wrong, CocoExport"
            
        return result.passed_value

    def _import(self)->bool:
        """Není implementováno"""
        
        raise "Not Implemented"
    
    def __to_json_yolo(self, invoice:Invoice)->OperationResult:
        #filtrace spanů na základě bbox zda je na stránce a také tagu
        filtered = []
        w_img, h_img = _A4_W_PX, _A4_H_PX

        for span in invoice._spans:
            if(span.tag.code == 0 or span.tag in SPAN_TAGS_TO_IGNORE
               or span.b_box[0] > w_img or span.b_box[2] > w_img 
               or span.b_box[0] < 0 or span.b_box[2] < 0

               or span.b_box[1] > h_img or span.b_box[3] > h_img
               or span.b_box[1] < 0 or span.b_box[3] < 0):
               
                continue
            
            filtered.append((span.tokens, span.b_box, span.tag.code))  


        _, spans_boxes, spans_tag_list = map(list, zip(*filtered)) if filtered else ([], [], [])

        yolo_str = ""

        for i, (box, tag) in enumerate(zip(spans_boxes, spans_tag_list)):            
            bbox_width = abs(box[2] - box[0])
            bbox_height = abs(box[3] - box[1])

            center_x = box[0] + bbox_width/2.0
            center_y = box[1] + bbox_height/2.0

            yolo_str += f'{tag} {center_x/w_img} {center_y/h_img} {bbox_width/w_img} {bbox_height/h_img} \n'
        
        return OperationResult(True, yolo_str)