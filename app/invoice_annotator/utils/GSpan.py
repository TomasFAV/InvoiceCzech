from dataclasses import dataclass
from invoice_annotator.utils.consts import DEFAULT_SPAN_COLOR
from invoices_generator.core.span import span


@dataclass
class GSpan(span):

    color: tuple[int, int, int] = DEFAULT_SPAN_COLOR
    visible:bool = True

    def get_color_hex(self)->str:
        return "#%02x%02x%02x" % self.color
