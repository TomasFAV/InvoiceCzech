from typing import List

from dataclasses import dataclass, field

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.enumerates.token_tags import TOKEN_TAGS_TO_IGNORE
from invoice_annotator.utils.GSegment import GSegment
from invoice_annotator import AppData
from invoice_annotator.utils.GRelationship import GRelationship
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
from invoices_generator.core.enumerates.span_tags import span_tags

@dataclass
class GInvoice(DInvoice):


    _segments: list[GSegment] = field(default_factory=list)

    _selected_tokens: list[GToken] = field(default_factory=list)
    _selected_spans: list[GSpan] = field(default_factory=list)
    _selected_segments: list[GSegment] = field(default_factory=list)


    #---------------PŘEPIS DĚDĚNÝCH METOD EXTRAKCE-------------------
    def to_json_layoutlmv3(self) -> str:
        tokens, tokens_boxes, tokens_tag_list = ([], [], []) if not self._tokens else map(list, zip(*(
        (w.text, w.b_box, w.tag.code) for w in self._tokens if w.tag.code not in TOKEN_TAGS_TO_IGNORE)))

        spans = []
        spans_boxes = []
        spans_tag_list = []

        for span in self._spans:
            span_tokens = []
            for token_id in span.tokens:
                for index, s_token in enumerate(self._tokens):
                    if(token_id == s_token.id):
                        span_tokens.append(index)
                        break

            spans.append(span_tokens)
            spans_boxes.append(span.b_box)
            spans_tag_list.append(span.tag.code)
                
        segments_boxes, segments_tag_list = ([], []) if not self._segments else map(list, zip(*(
        (w.b_box, w.tag.code) for w in self._segments)))
            
        
        output = { 
                        "tokens":{  "tokens": tokens,
                                    "boxes": tokens_boxes,
                                    "tags":tokens_tag_list
                        },
                        "spans":{
                            "token_ids": spans,
                            "boxes": spans_boxes,
                            "tags": spans_tag_list
                        },
                        "segments":{
                            "boxes":segments_boxes,
                            "tags":segments_tag_list
                        }
        }

        return output  

    #---------------PŘEPIS DĚDĚNÝCH METOD EXTRAKCE-------------------
    #--------------------------KONEC---------------------------------

    # -------------------------- pomocné metody --------------------------
    #--- práce se strukturami reprezentující informace na faktuře ---

    def clear_spans(self) -> None:
        self._spans = list()

    #--- práce se strukturami reprezentující informace na faktuře ---
    #-------------------------KONEC----------------------------------

    #vrací první nalezený
    def _get_span_text_by_tag(self, span_tag:span_tags) -> str:
        for span in self._spans:
            if(span.tag == span_tag):
                return self._get_span_text(span)

        return ""

    def _get_span_text(self, span:GSpan) -> str:
        token_ids: list[int] = span.tokens

        text: list[str] = []

        for token_id in token_ids:
            text.append(AppData.AppData.invoice.get_token_by_id(token_id).text)

        return " ".join(text)

    def _find_all_spans(self, span_tag:span_tags)->list[GSpan]:
        spans: list[GSpan] = []

        for span in self._spans:
            if(span.tag == span_tag):
                spans.append(span)

        return spans

    #vrátí všechny vztahy obsahující span
    def _find_relationships(self, span:GSpan)->List[GRelationship]:
        relationships: list[GRelationship] = []

        for rel in self._relationships:
            if rel.span_a == span or rel.span_b == span:
                relationships.append(rel)

        return relationships


    # -------------------------- pomocné metody --------------------------
    # -----------------------------KONEC----------------------------------