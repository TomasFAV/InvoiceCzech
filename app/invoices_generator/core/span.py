from dataclasses import dataclass, field
from typing import List
from app.invoices_generator.core.enumerates.span_tags import span_tags


@dataclass
class span:
    
    
    b_box: tuple[float, float, float, float]
    tag: span_tags
    tokens:List[int] = field(default_factory=list)
