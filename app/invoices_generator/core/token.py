from dataclasses import dataclass
from app.invoices_generator.core.enumerates.token_tags import token_tags


@dataclass
class token:
    
    text:str
    b_box: tuple[float, float, float, float]
    tag: token_tags
