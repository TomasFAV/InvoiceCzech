import os
from pathlib import Path

from invoice_annotator.Session import Session
from invoice_annotator.utils.GTesseract import GTesseract, TesseractConfig
from invoice_annotator.view.components.BoundingBoxLayer import Drawable
from shared.OperationResult import OperationResult
from invoice_annotator.utils.consts import DEFAULT_SEGMENT_COLOR, DEFAULT_SPAN_COLOR, DEFAULT_TOKEN_COLOR, SELECTED_SEGMENT_COLOR
from invoice_annotator.utils.consts import SELECTED_SPAN_COLOR, SELECTED_TOKEN_COLOR, SET_SEGMENT_COLOR, SET_SPAN_COLOR, SET_TOKEN_COLOR
from invoice_annotator.utils.GSegment import GSegment
from invoices_generator.core.enumerates.segment_tags import segment_tags
from invoice_annotator.AI.LiltModel import LiltModel
from invoice_annotator.controller.Controller import Controller
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
from invoice_annotator.utils.union_bbox import union_bbox
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.enumerates.token_tags import token_tags


class HomePageController(Controller):


    def __init__(self, session:Session):
        super().__init__(session)
        self.pytesseract: GTesseract = GTesseract(TesseractConfig("ces"))
        self.ai_assistant: LiltModel = LiltModel()



    def open_invoice(self, file_path:str, *kwargs) -> OperationResult:

        if not Path(file_path).exists():
            return

        self.session.reset()

        #pokusim se kouknout jestli neni v metadata_layoutlmv3
        if(not self.load_invoice(file_path) and not self.extract_img_text(file_path, True)):
            return OperationResult(False)

        return OperationResult(True, file_path)

    def load_invoice(self, file)->bool:
        #podivam se do rodice, jestli nema soubor metadata_layoutlmv3.jsonl
        file_path = Path(file)
        parent_path = file_path.parent.parent.absolute()

        layoutlmv3_path = Path(os.path.join(parent_path, "metadata_layoutlmv3.jsonl"))
        if not layoutlmv3_path.exists():
            return False
        
        layout_result:bool = self.session.invoice.from_layoutlmv3(layoutlmv3_path, file_path)

        donut_path = Path(os.path.join(parent_path, "metadata_donut.jsonl"))
        if not donut_path.exists():
            return False

        donut_result:bool = self.session.invoice.from_donut(donut_path, file_path)

        return layout_result and donut_result #buď se podařilo načíst obojí => True, jinak False


    def extract_img_text(self, img_path:str, preprocess_with_ai:bool = False) -> bool:        
        text, bbox, bbox_norm = self.pytesseract.extract_text(Path(img_path))
        tags = self.ai_assistant.predict(text, bbox_norm)
        #tags = list()

        for i, _ in enumerate(bbox):
            tag:token_tags =  token_tags.from_id(tags[i]) if i < len(tags) else token_tags.O
            color = DEFAULT_TOKEN_COLOR if tag == token_tags.O else SET_TOKEN_COLOR 
            self.append_token(GToken(None, text[i], bbox[i], token_tags.from_id(tags[i]) if i < len(tags) else token_tags.O, color))

        return True

    def toogle(self, item:Drawable, selected_items:list[Drawable], default_color:str, selected_color:str, set_color:str)->None:
        if item not in selected_items:
            selected_items.append(item)
            item.color = selected_color  # aktivní výběr
        elif item.tag.code != 0:
            item.color = set_color  # má jiný tag než O -> „potvrzený“
            selected_items.remove(item)
        else:
            item.color = default_color  # tag O -> vrátit do defaultu
            selected_items.remove(item)

    def toogle_token(self, id:int) -> OperationResult:
        token:GToken|None = self.get_token_by_id(id).passed_value
        if not token or not token.visible:
            return OperationResult(False)
        
        self.toogle(token, self.get_selected_tokens().passed_value, DEFAULT_TOKEN_COLOR, SELECTED_TOKEN_COLOR, SET_TOKEN_COLOR)

        return OperationResult(True)

    
    def toogle_span(self, id:int) -> OperationResult:
        span:GSpan|None = self.get_span_by_id(id).passed_value
        if not span or not span.visible: 
            return OperationResult(False)
        
        self.toogle(span, self.get_selected_spans().passed_value, DEFAULT_SPAN_COLOR, SELECTED_SPAN_COLOR, SET_SPAN_COLOR)

        return OperationResult(True)

    def toogle_segment(self, id:int):
        segment:GSegment|None = self.get_segment_by_id(id).passed_value
        if not segment or not segment.visible:
            return OperationResult(False)

        self.toogle(segment, self.get_selected_segments().passed_value, DEFAULT_SEGMENT_COLOR, SELECTED_SEGMENT_COLOR, SET_SEGMENT_COLOR)

        return OperationResult(True)

    def apply_tag(self, items:list[Drawable], tag: token_tags | span_tags | segment_tags|None, default_tag:token_tags | span_tags | segment_tags, default_color:str, set_color:str):
        for item in items:
            if tag:
                item.tag = tag
            item.color = default_color if tag == default_tag else set_color

        items.clear()
        return True

    def apply_tag_to_token_selection(self, tag: token_tags)->OperationResult:
        ok = self.apply_tag(self.get_selected_tokens().passed_value, tag=tag, default_tag=token_tags.O, default_color=DEFAULT_TOKEN_COLOR, set_color=SET_TOKEN_COLOR)
        return OperationResult(ok)
    
    def apply_tag_to_span_selection(self, tag:span_tags)->OperationResult:
        if len(self.get_selected_spans().passed_value) == 0 and len(self.get_selected_tokens().passed_value) != 0:
            selected_tokens = self.get_selected_tokens().passed_value
            self.append_span(GSpan(None, union_bbox([token.b_box for token in selected_tokens]), tag, [token.id for token in selected_tokens],SET_SPAN_COLOR))

            ok = self.apply_tag(selected_tokens, tag=None, default_tag=token_tags.O, default_color=DEFAULT_TOKEN_COLOR, set_color=SET_TOKEN_COLOR)
        else:
            ok = self.apply_tag(self.get_selected_spans().passed_value, tag=tag, default_tag=span_tags.O, default_color=DEFAULT_SPAN_COLOR, set_color=SET_SPAN_COLOR) 
        return OperationResult(ok)
    
    def apply_tag_to_segment_selection(self, tag:segment_tags)->OperationResult:
        ok = self.apply_tag(self.get_selected_segments().passed_value, tag=tag, default_tag=segment_tags.O, default_color=DEFAULT_SEGMENT_COLOR, set_color=SET_SEGMENT_COLOR)
        return OperationResult(ok)

    def create_spans_from_annotated_tokens(self)->None:
        for token in self.get_tokens().passed_value:
            if token.tag == token_tags.O or token.tag.code % 2 == 0:
                continue

            if not self.is_in_spans(token).passed_value:
                self.append_span(GSpan(None, token.b_box, span_tags.from__token_id(token.tag.code), [token.id], SET_SPAN_COLOR))