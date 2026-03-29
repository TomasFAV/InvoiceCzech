from enum import Enum
import json
from pathlib import Path
from typing import Any
from common.invoice.models.GSegment import GSegment
from common.invoice.models.GSpan import GSpan
from common.invoice.models.GToken import GToken
from common.utils.consts import DEFAULT_SEGMENT_COLOR, DEFAULT_TOKEN_COLOR, SET_SEGMENT_COLOR, SET_SPAN_COLOR, SET_TOKEN_COLOR
from common.enumerates.SegmentTag import SegmentTag
from common.enumerates.SpanTag import SPAN_TAGS_TO_IGNORE, SpanTag
from common.enumerates.TokenTag import TOKEN_TAGS_TO_IGNORE, TokenTag
from common.invoice.models.Invoice import Invoice
from common.invoice.OperationResult import OperationResult
from common.invoice.Processors.IEProcessors.IEProcessor import IEProcessor

class LayoutLMV3IEConfig(Enum):
    WITH_TESSERACT = "WITH_TESSERACT"
    WITHOUT_TESSERACT = "WITHOUT_TESSERACCT"
    

class LayoutLMV3IEProcessor(IEProcessor):
        

    def _export(self, invoice:Invoice, option: LayoutLMV3IEConfig = LayoutLMV3IEConfig.WITH_TESSERACT)->dict[str, Any]:
        result: OperationResult = OperationResult(False)
        
        if(option == LayoutLMV3IEConfig.WITH_TESSERACT):
            result = self.__to_json_layoutlmv3_with_tesseract(invoice)
        elif(option == LayoutLMV3IEConfig.WITHOUT_TESSERACT):
            result = self.__to_json_layoutlmv3_without_tesseract(invoice)

        if(not result.ok):
            if isinstance(result.passed_value, str):
                raise result.passed_value
            else:
                raise "Something went wrong, LayoutLMV3Export"
            
        return result.passed_value

    def _import(self, invoice:Invoice, layoutlmv3_file_path: Path, invoice_file_path:Path)->bool:
        """
            Natáhne hodnoty do invoice_data
        """
        result:OperationResult = self.__invoice_from_layoutlmv3(invoice, layoutlmv3_file_path, invoice_file_path)

        if(result.ok):
            return result.passed_value
        
        return False    
    

    def __invoice_from_layoutlmv3(self,invoice:Invoice, layoutlmv3_path:Path, invoice_file_path:Path) -> OperationResult:
        """
        Načte tokeny, spany a segmenty z layoutlmv3 souboru a podle jména faktury
        """

        with open(layoutlmv3_path) as f:
            for line in f:
                record = json.loads(line)

                if record["file_name"] != invoice_file_path.name:
                    continue

                # --- načtení tokenů ---

                tokens = record["data"].get("tokens", None)
                
                if tokens:

                    tok_texts = tokens["tokens"]
                    tok_tags = tokens["tags"]
                    tok_boxes = tokens["boxes"]

                    for text, tag_id, box in zip(tok_texts, tok_tags, tok_boxes):
                        tag_id:TokenTag =  TokenTag.from_id(tag_id)
                        color = DEFAULT_TOKEN_COLOR if tag_id == TokenTag.O else SET_TOKEN_COLOR
                        
                        invoice.append_token(GToken(None, text, box, tag_id, color))


                # --- načtení spanů ---

                spans = record["data"].get("spans", None)

                if spans:

                    sp_tokens = spans["token_ids"]#[[id prvního tokenu spanu 1, id druhého tokenu spanu 1], [id prvního tokenu spanu 2,...], [...], ...]
                    sp_tags = spans["tags"]
                    sp_boxes = spans["boxes"]
                    
                    for tokens_orig, tag_id, box in zip(sp_tokens, sp_tags, sp_boxes):
                        tokens = [invoice._tokens[token_orig_id].id for token_orig_id in tokens_orig]
                        invoice.append_span(GSpan(None, box, SpanTag.from_id(tag_id), tokens,SET_SPAN_COLOR))


                # --- načtení segmentů ---
                segments = record["data"].get("segments", None)
                
                if segments:

                    seg_tags = segments["tags"]
                    seg_boxes = segments["boxes"]

                    for seg_id, box in zip(seg_tags, seg_boxes):
                        seg:SegmentTag =  SegmentTag.from_id(seg_id)
                        color = DEFAULT_SEGMENT_COLOR if seg_id == SegmentTag.O else SET_SEGMENT_COLOR
                        
                        invoice.append_segment(GSegment(None, box, seg, color))

                return OperationResult(True, True)
            
        return OperationResult(True, False)

    #je totožná pro všechny faktury
    def __to_json_layoutlmv3_with_tesseract(self, invoice:Invoice) -> OperationResult:
        """
            Jedná se o export do formátu layoutlmv3, kde proběhne ještě průnik bounding boxů a jejich obsahu spolu s tesseractem
        """

        span_tokens, span_boxes, span_tag_list, tokens, tokens_boxes, tokens_tag_list = self.invoice_ocr_aligner.intersect_tokens_tesseract(invoice)
        
        f_tokens, f_tokens_boxes, f_tokens_tag_list = [],[],[]
        f_span_tokens, f_span_boxes, f_span_tag_list = [],[],[]

        for tok, box, tag_id in zip(tokens, tokens_boxes, tokens_tag_list):
            tag = TokenTag.from_id(tag_id)

            if(tag in TOKEN_TAGS_TO_IGNORE):
                tag_id = TokenTag.O.code
            
            f_tokens.append(tok)
            f_tokens_boxes.append(box)
            f_tokens_tag_list.append(tag_id)

        for tok, box, tag_id in zip(span_tokens, span_boxes, span_tag_list):
            tag = SpanTag.from_id(tag_id)          

            if(tag in SPAN_TAGS_TO_IGNORE or tag == SpanTag.O):
                continue   
            
            f_span_tokens.append(tok)
            f_span_boxes.append(box)
            f_span_tag_list.append(tag_id)

        segments_boxes, segments_tag_list = ([], []) if not invoice._segments else map(list, zip(*(
        (w.b_box, w.tag.code) for w in invoice._segments)))

        output = { 
                        "tokens":{  "tokens": f_tokens,
                                    "boxes": f_tokens_boxes,
                                    "tags":f_tokens_tag_list
                        },
                        "spans":{
                            "token_ids": f_span_tokens,
                            "boxes": f_span_boxes,
                            "tags": f_span_tag_list
                        },
                        "segments":{
                            "boxes":segments_boxes,
                            "tags":segments_tag_list
                        }
        }

        return OperationResult(True, output)  

    def __to_json_layoutlmv3_without_tesseract(self, invoice:Invoice) -> dict[str, Any]:

        """
        Vytváří layoulmv3 data formát pouze z inforamcí na faktuře(tokeny, spany, segmenty). NEPROBÍHÁ intersection s tesseractem
        """

        tokens, tokens_boxes, tokens_tag_list = ([], [], []) if not invoice._tokens else map(list, zip(*(
        (w.text, w.b_box, w.tag.code) for w in invoice._tokens if w.tag.code not in TOKEN_TAGS_TO_IGNORE)))

        spans = []
        spans_boxes = []
        spans_tag_list = []

        for span in invoice._spans:
            span_tokens = []
            for token_id in span.tokens:
                for index, s_token in enumerate(invoice._tokens):
                    if(token_id == s_token.id):
                        span_tokens.append(index)
                        break

            spans.append(span_tokens)
            spans_boxes.append(span.b_box)
            spans_tag_list.append(span.tag.code)
                
        segments_boxes, segments_tag_list = ([], []) if not invoice._segments else map(list, zip(*(
        (w.b_box, w.tag.code) for w in invoice._segments)))
            
        
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

        return OperationResult(True, output)  