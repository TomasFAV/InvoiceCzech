from dataclasses import dataclass
from invoices_generator.core.segment import segment
from invoice_annotator.utils.consts import DEFAULT_SEGMENT_COLOR
from invoices_generator.core.enumerates import token_tags
from invoices_generator.core.enumerates.segment_tags import segment_tags

@dataclass
class GSegment(segment):
   
    color: tuple[int, int, int] = DEFAULT_SEGMENT_COLOR
    visible:bool = True

    
    

    def get_color_hex(self)->str:
        return "#%02x%02x%02x" % self.color