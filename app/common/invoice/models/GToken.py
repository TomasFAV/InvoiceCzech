from dataclasses import dataclass
from common.utils.consts import DEFAULT_TOKEN_COLOR
from common.Token import Token

@dataclass
class GToken(Token):

    color: tuple[int, int, int] = DEFAULT_TOKEN_COLOR
    visible:bool = True
    synthetic:bool = False

    def get_color_hex(self)->str:
        return "#%02x%02x%02x" % self.color