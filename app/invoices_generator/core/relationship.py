from dataclasses import dataclass
from app.invoices_generator.core.enumerates.relationship_types import relationship_types
from app.invoices_generator.core.enumerates.token_tags import token_tags

@dataclass
class relationship:
    
    span_a_index:int
    span_b_index:int
    type: relationship_types
