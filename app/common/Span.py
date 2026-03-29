from dataclasses import dataclass, field
from typing import List
from common.enumerates.SpanTag import SpanTag


@dataclass
class Span:
    
    id:int
    b_box: tuple[float, float, float, float]
    tag: SpanTag
    tokens:List[int] = field(default_factory=list)
