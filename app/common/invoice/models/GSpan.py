from dataclasses import dataclass
from common.utils.consts import DEFAULT_SPAN_COLOR
from common.Span import Span


@dataclass
class GSpan(Span):

    color: tuple[int, int, int] = DEFAULT_SPAN_COLOR
    visible:bool = True

    def get_color_hex(self)->str:
        return "#%02x%02x%02x" % self.color
