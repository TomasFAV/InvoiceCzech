import json
import os
import sys

from tkinter import messagebox, filedialog, simpledialog

import pytesseract

from sympy import O, true
from invoice_annotator.view.components.ImageCanvas import ImageCanvas
from shared.OperationResult import OperationResult
from invoice_annotator.utils.consts import DEFAULT_SEGMENT_COLOR, DEFAULT_SPAN_COLOR, DEFAULT_TOKEN_COLOR, SELECTED_SEGMENT_COLOR, SELECTED_SPAN_COLOR, SELECTED_TOKEN_COLOR, SET_SEGMENT_COLOR, SET_SPAN_COLOR, SET_TOKEN_COLOR
from invoice_annotator.utils.GSegment import GSegment
from invoices_generator.core.enumerates.segment_tags import segment_tags
from invoice_annotator.AI.LiltModel import LiltModel
from invoice_annotator.controller.Controller import Controller
from invoice_annotator.AppData import AppData
from invoice_annotator.enumerates.DataSource import DataSource
from invoice_annotator.utils.GRelationship import GRelationship
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
from invoice_annotator.utils.union_bbox import union_bbox
import tkinter.filedialog

from PIL import Image
from pytesseract import Output

from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import SPAN_TAGS_TO_IGNORE, span_tags
from invoices_generator.core.enumerates.token_tags import token_tags
from pathlib import Path


class HomePageController(Controller):


    def __init__(self):

        self.ai_assistant: LiltModel = LiltModel()



    def open_invoice(self, file_path:str, *kwargs) -> OperationResult:

        if not Path(file_path).exists():
            return

        AppData.reset()

        self.extract_img_informations(file_path)

        #pokusim se kouknout jestli neni v metadata_layoutlmv3
        if(not self.load_invoice(file_path) and not self.extract_img_text(file_path, true)):
            return OperationResult(False)

        return OperationResult(True, file_path)


    def extract_img_informations(self, img_path:str) -> None:
        AppData.original_img_width, AppData.original_img_height = Image.open(img_path).size
        AppData.invoice._A4_W_PX, AppData.invoice._A4_H_PX = Image.open(img_path).size

    def load_invoice(self, file)->bool:
        #podivam se do rodice, jestli nema soubor metadata_layoutlmv3.jsonl
        file_path = Path(file)
        parent_path = file_path.parent.parent.absolute()

        layoutlmv3_path = Path(os.path.join(parent_path, "metadata_layoutlmv3.jsonl"))
        if not layoutlmv3_path.exists():
            return False
        
        donut_path = Path(os.path.join(parent_path, "metadata_donut.jsonl"))
        if not donut_path.exists():
            return False
        
        with open(layoutlmv3_path) as f:
            for line in f:
                record = json.loads(line)

                if record["file_name"] != file_path.name:
                    continue

                # --- načtení tokenů ---

                tokens = record["data"].get("tokens", None)
                
                if tokens:

                    tok_texts = tokens["tokens"]
                    tok_tags = tokens["tags"]
                    tok_boxes = tokens["boxes"]

                    for text, tag_id, box in zip(tok_texts, tok_tags, tok_boxes):
                        tag_id:token_tags =  token_tags.from_id(tag_id)
                        color = DEFAULT_TOKEN_COLOR if tag_id == token_tags.O else SET_TOKEN_COLOR
                        
                        AppData.invoice.append_token(GToken(None, text, box, tag_id, color))


                # --- načtení spanů ---

                spans = record["data"].get("spans", None)

                if spans:

                    sp_tokens = spans["token_ids"]#[[id prvního tokenu spanu 1, id druhého tokenu spanu 1], [id prvního tokenu spanu 2,...], [...], ...]
                    sp_tags = spans["tags"]
                    sp_boxes = spans["boxes"]
                    
                    for tokens_orig, tag_id, box in zip(sp_tokens, sp_tags, sp_boxes):
                        tokens = [AppData.invoice._tokens[token_orig_id].id for token_orig_id in tokens_orig]
                        AppData.invoice.append_span(GSpan(None, box, span_tags.from_id(tag_id), tokens,SET_SPAN_COLOR))


                # --- načtení segmentů ---
                segments = record["data"].get("segments", None)
                
                if segments:

                    seg_tags = segments["tags"]
                    seg_boxes = segments["boxes"]

                    for seg_id, box in zip(seg_tags, seg_boxes):
                        seg:segment_tags =  segment_tags.from_id(seg_id)
                        color = DEFAULT_SEGMENT_COLOR if seg_id == segment_tags.O else SET_SEGMENT_COLOR
                        
                        AppData.invoice.append_segment(GSegment(None, box, seg, color))

                break

        with open(donut_path, "r", encoding="utf-8") as f:
            for line in f:
                raw_data = json.loads(line)

                if raw_data["file_name"] != file_path.name:
                    continue
                
                ground_truth:dict = raw_data.get("ground_truth", None)
                if not ground_truth or not isinstance(ground_truth, dict):
                    return False
                
                data:dict = ground_truth.get("gt_parse", None)
                if not data or not isinstance(data, dict):
                    return False


                AppData.invoice.invoice_number = data.get("invoice_number", "")
                
                AppData.invoice.supplier.register_id = data.get("supp_register_id", "")
                AppData.invoice.supplier.tax_id = data.get("supp_tax_id", "")

                AppData.invoice.customer.register_id = data.get("cust_register_id", "")
                AppData.invoice.customer.tax_id = data.get("cust_tax_id", "")

                AppData.invoice.issue_date = data.get("issue_date", "")
                AppData.invoice.taxable_supply_date = data.get("taxable_supply_date", "")
                AppData.invoice.due_date = data.get("due_date", "")

                AppData.invoice.payment_type = data.get("payment_type", "")
                AppData.invoice.bank_account_number = data.get("bank_account_number", "")
                AppData.invoice.bank_account.BIC = data.get("bic", "")
                AppData.invoice.IBAN = data.get("iban", "")
                AppData.invoice.variable_symbol = data.get("variable_symbol", "")
                AppData.invoice.const_symbol = data.get("const_symbol", "")
                AppData.invoice.total_price = data.get("total", "")        

                return True
        
        return False

    def extract_img_text(self, img_path:str, preprocess_with_ai:bool = False) -> bool:        
        lang = 'ces'

        if sys.platform == "linux":
            pass
        elif sys.platform == "win32":
            pytesseract.pytesseract.tesseract_cmd = r'E:\user\plocha\BP\packages\tesseract.exe'
        else:
            return False
        
        data = pytesseract.image_to_data(Image.open(img_path), lang=lang, output_type=Output.DICT)
        
        bbox = [((int)(l),(int)(t),(int)((l+w)),(int)((t+h)))  for l,t,w,h,c in zip(data["left"], data["top"], data["width"], data["height"], data["conf"]) if c != -1 and c > 30]
        text = [t  for t,c in zip(data["text"], data["conf"]) if c != -1 and c > 30]


        bbox_norm = [((float)(box[0])/(AppData.original_img_width),
                      (float)(box[1])/(AppData.original_img_height),
                      (float)(box[2])/(AppData.original_img_width),
                      (float)(box[3])/(AppData.original_img_height)) for box in bbox]

        tags = self.ai_assistant.predict(text, bbox_norm)

        for i, _ in enumerate(bbox):
            tag:token_tags =  token_tags.from_id(tags[i]) if i < len(tags) else token_tags.O
            color = DEFAULT_TOKEN_COLOR if tag == token_tags.O else SET_TOKEN_COLOR 
            AppData.invoice.append_token(GToken(None, text[i], bbox[i], token_tags.from_id(tags[i]) if i < len(tags) else token_tags.O, color))

        return True

    def reset_token(self, token:GToken) -> OperationResult:
        for tok in AppData.invoice._tokens:
            if(tok == token):
                tok.tag = token_tags.O
                tok.color = DEFAULT_TOKEN_COLOR

        return OperationResult(True) 

    def remove_token(self, token:GToken) -> OperationResult:
        ok = AppData.invoice.remove_token(token)
        return OperationResult(ok) 

    def remove_span(self, span:GSpan) -> OperationResult:
        ok = AppData.invoice.remove_span(span)
        return OperationResult(ok) 

    def remove_segment(self, segment:GSegment) -> OperationResult:
        ok = AppData.invoice.remove_segment(segment)
        return OperationResult(ok) 


    def select(self, mouse_position: tuple[int, int], variant: DataSource, tokens_visible: bool, spans_visible: bool, segments_visible: bool,
               canvas:ImageCanvas) -> OperationResult:
        if (variant == DataSource.TOKENS or variant == DataSource.SPANS) and tokens_visible:
            # V režimu "tokens"/"spans" vybíráme jednotlivé tokeny (stav pro stavbu spanu)
            ok = self.select_token(mouse_position, canvas)
            return OperationResult(ok)
        elif variant == DataSource.RELATIONSHIP and spans_visible:
            # V režimu "relationships" vybíráme celé spany
            ok = self.select_span(mouse_position, canvas)
            return OperationResult(ok)
        elif variant == DataSource.SEGMENTS and segments_visible:
            # V režimu "relationships" vybíráme celé spany
            ok = self.select_segment(mouse_position, canvas)
            return OperationResult(ok)
        
        else:
            
            return OperationResult(False)

    def remove_relationship(self, relationship: GRelationship) -> OperationResult:
        if relationship in AppData.invoice._relationships:
            AppData.invoice._relationships.remove(relationship)
            return OperationResult(True)
        else:
            return OperationResult(False)
        

    def select_token(self, mouse_position: tuple[int, int], canvas:ImageCanvas) -> bool:
        token = self.get_token_by_bounding_box(mouse_position, canvas)

        if token is not None and token.visible:
            # toggle logika pro token
            if token not in AppData.invoice._selected_tokens:
                token.color = SELECTED_TOKEN_COLOR  # aktivní výběr (červená)
                AppData.invoice._selected_tokens.append(token)
            elif token.tag != token_tags.O:
                token.color = SET_TOKEN_COLOR  # má jiný tag než O -> „potvrzený“ (zelená)
                AppData.invoice._selected_tokens.remove(token)
            else:
                token.color = DEFAULT_TOKEN_COLOR  # tag O -> vrátit do defaultu (černá)
                AppData.invoice._selected_tokens.remove(token)

            return True

        # klik mimo -> aktualizuj barvy všech aktuálně vybraných tokenů
        for selected_token in list(AppData.invoice._selected_tokens):
            token:GToken = AppData.invoice.get_token_by_id(selected_token.id)
            if not token:
                return False
            
            token.color = SET_TOKEN_COLOR if token.tag != token_tags.O else DEFAULT_TOKEN_COLOR

        AppData.invoice._selected_tokens.clear()

        return True 

    def select_span(self, mouse_position: tuple[int, int], canvas:ImageCanvas) -> None:
        span = self.get_span_by_bounding_box(mouse_position, canvas)


        if span is not None and span.visible:
            # toggle logika pro span
            if span not in AppData.invoice._selected_spans:
                span.color = SELECTED_SPAN_COLOR  # vybraný (červená)
                AppData.invoice._selected_spans.append(span)
            else:
                span.color = SET_SPAN_COLOR  # zrušený výběr (modrá) – pokud chceš jinak
                AppData.invoice._selected_spans.remove(span)
            
            return True

        # klik mimo -> obnov barvy u aktuálně vybraných spanů
        for selected_span in list(AppData.invoice._selected_spans):
            span:GSpan = AppData.invoice.get_span_by_id(selected_span.id)
            if not span:
                return False
            
            span.color = SET_TOKEN_COLOR if span.tag != token_tags.O else DEFAULT_TOKEN_COLOR
        
        return True

    def select_segment(self, mouse_position: tuple[int, int], canvas:ImageCanvas) -> None:
        segment = self.get_segment_by_bounding_box(mouse_position, canvas)

        if segment is not None and segment.visible:
            # toggle logika pro token
            if segment not in AppData.invoice._selected_segments:
                segment.color = SELECTED_SEGMENT_COLOR  # aktivní výběr (červená)
                AppData.invoice._selected_segments.append(segment)
            elif segment.tag != segment_tags.O:
                segment.color = SET_SEGMENT_COLOR  # má jiný tag než O -> „potvrzený“ (zelená)
                AppData.invoice._selected_segments.remove(segment)
            else:
                segment.color = DEFAULT_SEGMENT_COLOR  # tag O -> vrátit do defaultu (černá)
                AppData.invoice._selected_segments.remove(segment)

            return True

        # klik mimo -> aktualizuj barvy všech aktuálně vybraných tokenů
        for selected_segment in list(AppData.invoice._selected_segments):
            segment:GSegment = AppData.invoice.get_segment_by_id(selected_segment.id)
            if not segment:
                return False
            
            segment.color = SET_TOKEN_COLOR if segment.tag != token_tags.O else DEFAULT_TOKEN_COLOR

        return True

    def get_span_by_bounding_box(self, mouse_position:tuple[int, int], canvas:ImageCanvas) -> GSpan | None:
        mx, my = mouse_position

        # Scale a posun: obraz -> plátno
        scale = canvas.base_img_scale * canvas.image_zoom
        # Inverzní transformace: plátno -> obraz (neškálované souřadnice)
        ix, iy = canvas._canvas_to_image(mx, my)

        threshold_img: float = max(1, 2 / scale)

        for id, span in enumerate(AppData.invoice._spans):
            x1, y1, x2, y2 = span.b_box  # očekává se v obrazových souřadnicích

            if (x1 - threshold_img <= ix <= x2 + threshold_img and
                    y1 - threshold_img <= iy <= y2 + threshold_img):

                return span

        return None




    def get_token_by_bounding_box(self, mouse_position:tuple[int, int],canvas:ImageCanvas) -> GToken | None:
        mx, my = mouse_position

        # Scale a posun: obraz -> plátno
        scale = canvas.base_img_scale * canvas.image_zoom
        # Inverzní transformace: plátno -> obraz (neškálované souřadnice)
        ix, iy = canvas._canvas_to_image(mx, my)

        threshold_img: float = max(1, 2 / scale)

        for id, token in enumerate(AppData.invoice._tokens):
            x1, y1, x2, y2 = token.b_box  # očekává se v obrazových souřadnicích

            if (x1 - threshold_img <= ix <= x2 + threshold_img and
                    y1 - threshold_img <= iy <= y2 + threshold_img
                    and token.visible):
                return token

        return None
    
    def get_segment_by_bounding_box(self, mouse_position:tuple[int, int], canvas:ImageCanvas) -> GSegment | None:
        mx, my = mouse_position

        # Scale a posun: obraz -> plátno
        scale = canvas.base_img_scale * canvas.image_zoom
        # Inverzní transformace: plátno -> obraz (neškálované souřadnice)
        ix, iy = canvas._canvas_to_image(mx, my)

        threshold_img: float = max(1, 2 / scale)

        for id, segment in enumerate(AppData.invoice._segments):
            x1, y1, x2, y2 = segment.b_box  # očekává se v obrazových souřadnicích

            if (x1 - threshold_img <= ix <= x2 + threshold_img and
                    y1 - threshold_img <= iy <= y2 + threshold_img
                    and segment.visible):
                return segment

        return None

    def create_token(self, bbox: tuple[float, float, float, float], text: str) -> OperationResult:
        token = GToken(
            None,
            text,
            bbox,
            token_tags.O,
            DEFAULT_TOKEN_COLOR,
            synthetic=True
        )
        AppData.invoice.append_token(token)
        return OperationResult(True)

    def create_segment(self, bbox: tuple[float, float, float, float]) -> OperationResult:
        segment = GSegment(None, bbox,segment_tags.O, DEFAULT_SEGMENT_COLOR)

        AppData.invoice.append_segment(segment)
        return OperationResult(True)

    def set_selected_tokens_token_tag(self, tag:token_tags) -> OperationResult:
        for selected_token in AppData.invoice._selected_tokens:

            selected_token.tag = tag
            if(tag == token_tags.O):
                selected_token.color = DEFAULT_TOKEN_COLOR
            else:    
                selected_token.color = SET_TOKEN_COLOR

        AppData.invoice._selected_tokens.clear()

        return OperationResult(True)
    
    def set_selected_tokens_span_tag(self, tag:span_tags) -> OperationResult:
        if(len(AppData.invoice._selected_tokens) <= 0):
            messagebox.showwarning("Chyba", "Nemáte vybrané žádné tokeny k oštítkování.")
            return OperationResult(False)

        if(len([tok for tok in AppData.invoice._selected_tokens if tok.tag == token_tags.O]) > 0):
            messagebox.showwarning("Chyba", "Mezi vybranými tokeny jsou tokeny bez štítku")
            return OperationResult(False)

        for selected_token in AppData.invoice._selected_tokens:
            if(selected_token.tag == token_tags.O):
                selected_token.color = DEFAULT_TOKEN_COLOR
            else:
                selected_token.color = SET_TOKEN_COLOR

        new_id = AppData.invoice.alloc_span_id()

        AppData.invoice.append_span(GSpan(new_id, union_bbox([sel_token.b_box for sel_token in AppData.invoice._selected_tokens]),tag,[sel_token.id for sel_token in AppData.invoice._selected_tokens], SET_SPAN_COLOR))
        AppData.invoice._selected_tokens.clear()

        return OperationResult(True)

    def set_selected_relationship_tag(self, tag: relationship_types) -> OperationResult:
        for selected_span in AppData.invoice._selected_spans:
            selected_span.color = SET_SPAN_COLOR

        if (len(AppData.invoice._selected_spans) != 2):
            messagebox.showerror("Chyba", "Při nastavování binárních vztahů musí být vždy označeny pouze dva spany.")
            AppData.invoice._selected_spans.clear()
            return OperationResult(False)

        AppData.invoice.append_relationship(
            GRelationship(None, span_a=AppData.invoice._selected_spans[0], span_b = AppData.invoice._selected_spans[1],type=tag)
        )

        AppData.invoice._selected_spans.clear()

        return OperationResult(True)

    def set_selected_segments_segment_tag(self, tag: segment_tags) -> OperationResult:
        for selected_segment in AppData.invoice._selected_segments:

            selected_segment.tag = tag
            if(tag == segment_tags.O):
                selected_segment.color = DEFAULT_SEGMENT_COLOR
            else:    
                selected_segment.color = SET_SEGMENT_COLOR


        AppData.invoice._selected_segments.clear()

        return OperationResult(True)

    def create_spans_from_labeled_tokens(self) -> None:
        if(not AppData.invoice):
            messagebox.showerror("Chyba", "Instance třídy invoice není naplněna.")

        tokens = [token for token in AppData.invoice._tokens if
                  token.tag != token_tags.O and token.tag.code % 2 == 1]  # tokeny, které začínají B_

        if (len(tokens) <= 0):
            messagebox.showwarning("Chyba", "Nejsou oštítkovány, žádné tokeny tagy b_...")
            return

        for token in tokens:
            if(not AppData.invoice.is_in_spans(token)):
                span_tag = [tag for tag in list(span_tags) if tag.ref == token.tag][0] #vždy bude jednoprvkové pole
                new_id:int = AppData.invoice.alloc_span_id()
                AppData.invoice.append_span(GSpan(new_id, token.b_box, span_tag, [token.id], SET_SPAN_COLOR))


    def reset_token_tags(self, *kwargs) -> OperationResult:
        for token in AppData.invoice._tokens:
            token.tag = token_tags.O
            token.color = DEFAULT_TOKEN_COLOR
        
        AppData.invoice.clear_spans()

        return OperationResult(True)

    # -- Pomocné ---------------------------------------------------------------
