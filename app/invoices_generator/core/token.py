from dataclasses import dataclass
from invoices_generator.core.enumerates.token_tags import token_tags


@dataclass
class token:
    
    id:int
    text:str
    b_box: tuple[float, float, float, float]
    tag: token_tags
