from dataclasses import dataclass
from common.Segment import Segment
from common.utils.consts import DEFAULT_SEGMENT_COLOR

@dataclass
class GSegment(Segment):
   
    color: tuple[int, int, int] = DEFAULT_SEGMENT_COLOR
    visible:bool = True

    
    

    def get_color_hex(self)->str:
        return "#%02x%02x%02x" % self.color