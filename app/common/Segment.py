from dataclasses import dataclass, field
from typing import List
from common.enumerates import SegmentTag
from common.enumerates.SpanTag import SpanTag


@dataclass
class Segment:

    #důležité informace
    id:int
    b_box: tuple[float, float, float, float]
    tag: SegmentTag