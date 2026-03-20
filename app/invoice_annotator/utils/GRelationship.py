from dataclasses import dataclass

from invoices_generator.core.relationship import relationship
from invoice_annotator.utils.GSpan import GSpan
from invoices_generator.core.enumerates.relationship_types import relationship_types


@dataclass
class GRelationship(relationship):
    ...
