from dataclasses import dataclass
from common.enumerates.TokenTag import TokenTag


@dataclass
class Token:
    
    id:int
    text:str
    b_box: tuple[float, float, float, float]
    tag: TokenTag
