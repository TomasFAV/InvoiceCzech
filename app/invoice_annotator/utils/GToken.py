from dataclasses import dataclass
from invoice_annotator.utils.consts import DEFAULT_TOKEN_COLOR
from invoices_generator.core.token import token

@dataclass
class GToken(token):

    color: tuple[int, int, int] = DEFAULT_TOKEN_COLOR
    visible:bool = True
    synthetic:bool = False

    def get_color_hex(self)->str:
        return "#%02x%02x%02x" % self.color