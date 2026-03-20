from dataclasses import dataclass
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.token_tags import token_tags

@dataclass
class relationship:
    
    id:int
    span_a_index:int
    span_b_index:int
    type: relationship_types
