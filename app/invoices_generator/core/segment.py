from dataclasses import dataclass, field
from typing import List
from invoices_generator.core.enumerates import segment_tags
from invoices_generator.core.enumerates.span_tags import span_tags


@dataclass
class segment:

    #důležité informace
    id:int
    b_box: tuple[float, float, float, float]
    tag: segment_tags