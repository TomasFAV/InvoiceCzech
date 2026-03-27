from copy import copy
import json
from pathlib import Path
from invoice_annotator.utils.consts import DEFAULT_SEGMENT_COLOR, DEFAULT_TOKEN_COLOR, SET_SEGMENT_COLOR, SET_SPAN_COLOR, SET_TOKEN_COLOR
from invoices_generator.core.enumerates.segment_tags import segment_tags
from invoice_annotator.utils.GSegment import GSegment
from invoice_annotator.utils.GToken import GToken
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GRelationship import GRelationship


from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import List


from jinja2 import Environment, FileSystemLoader

from invoices_generator.core.enumerates.span_tags import SPAN_TAGS_TO_IGNORE, span_tags
from invoices_generator.utility.json_serializable import json_serializable
from invoices_generator.core.enumerates.token_tags import TOKEN_TAGS_TO_IGNORE, token_tags

from invoices_generator.utility.utils import get_dimensions_symetry, get_iou, get_tesseract_words, merge_bboxes


@dataclass
class Invoice(json_serializable, ABC):
    """
    Abstraktní třída faktury, která je děděná třídou DInvoice (Data Invoice) a třídou GInvoice (Graphical Invoice).
    Obsahuje metody pro práci s tokeny/spany/vztahy faktury
    """

    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################  

   
    ###############################################################
    #            Informace potřebné pro tvorbu datasetu           # 
    ###############################################################

    _tokens:List[GToken] = field(default_factory=list)
    _spans:List[GSpan] = field(default_factory=list)
    _relationships: List[GRelationship] = field(default_factory=list)
    _segments: List[GSegment] = field(default_factory=list)

    #alokace id
    _next_token_id:int = 0
    _next_span_id: int = 0
    _next_relationship_id: int = 0
    _next_segment_id: int = 0

    _A4_W_PX:int = 1654
    _A4_H_PX:int = 2338

    ###############################################################
    #                            KONEC                            # 
    ###############################################################

            
    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################
    
    def intersect_tokens_tesseract(self, img_path:str):

        """
        Vezme data na faktuře a sjednotí s daty z ocr
        
        Vstupní boxy (self._tokens) jsou v 0 - 1000, OCR je v pixelech.

        Výstupní boxy jsou v rozlišení fotky

        """


        # 1. Získání OCR dat z Tesseractu (v pixelech)

        tess_tokens, tess_boxes, tess_boxes_norm = get_tesseract_words(img_path)

        # 2. Mapování tagů pomocí IoU

        # Pracujeme v pixelech (tess_boxes_px vs self._tokens.b_box)

        raw_tags = []

        for i, t_box_px in enumerate(tess_boxes):

            best_tag = 0

            max_metric = 0

            for ann_token in self._tokens:

                # ann_token.b_box jsou pixely, t_box_px jsou pixely -> OK
                overlap = get_iou(t_box_px, ann_token.b_box) #maximálně plocha toho menšího z těch dvou bboxů
                relative_bbox_symetry = get_dimensions_symetry(t_box_px, ann_token.b_box)

                metric = overlap * relative_bbox_symetry

                if metric > max_metric:

                    max_metric = metric

                    best_tag = ann_token.tag.code

            #threshold
            if max_metric < 0.05:
                best_tag = 0

            raw_tags.append(best_tag)



        # 3. BIO korekce (zajišťuje správnou sekvenci B- a I-)
        spans_boxes = []
        spans_tags = []
        spans_token_ids = []
        
        span_temp_token_ids = []

        final_tags = []

        last_base_tag = None

        for tag in raw_tags:

            if tag == 0:
                if len(span_temp_token_ids) != 0:
                    bboxes = []
                    for i in span_temp_token_ids:
                        bboxes.append(tess_boxes[i])
                    
                    
                    #sp = span(merge_bboxes(bboxes),span_tags.from__token_id(final_tags[-1]), span_temp_token_ids)
                    
                    spans_boxes.append(merge_bboxes(bboxes))
                    spans_tags.append(span_tags.from__token_id(final_tags[-1]).code)
                    spans_token_ids.append(copy(span_temp_token_ids))
                    
                    span_temp_token_ids = []

                span_temp_token_ids.append(len(final_tags))
                final_tags.append(0)

                last_base_tag = None

                continue


            # Předpoklad: B- je liché, I- je tag + 1

            is_b_tag = (tag % 2 != 0)

            base_tag = tag if is_b_tag else tag - 1


            if base_tag == last_base_tag:

                span_temp_token_ids.append(len(final_tags))

                final_tags.append(base_tag + 1) # Vynutit I- tag

            else:

                if len(span_temp_token_ids) != 0:
                    bboxes = []
                    for i in span_temp_token_ids:
                        bboxes.append(tess_boxes[i])
                    
                    
                    #sp = span(None, merge_bboxes(bboxes),span_tags.from__token_id(final_tags[-1]), span_temp_token_ids)
                    
                    spans_boxes.append(merge_bboxes(bboxes))
                    spans_tags.append(span_tags.from__token_id(final_tags[-1]).code)
                    spans_token_ids.append(span_temp_token_ids)

                    
                    span_temp_token_ids = []

                span_temp_token_ids.append(len(final_tags))

                final_tags.append(base_tag) # Začít novým B- tagem

                last_base_tag = base_tag

        if len(span_temp_token_ids) != 0:
            bboxes = [tess_boxes[idx] for idx in span_temp_token_ids]


            spans_boxes.append(merge_bboxes(bboxes))
            spans_tags.append(span_tags.from__token_id(final_tags[-1]).code)
            spans_token_ids.append(span_temp_token_ids)

        return spans_token_ids, spans_boxes, spans_tags, tess_tokens, tess_boxes, final_tags
    


    #--------------------------------METODY EXPORTU FAKTUR ---------------------------------



    def to_json_donut(self)->dict:
        #projdu tokeny a pokud je tam span s tagem různým od 0 a neni jeho bounding box mimo, tak ho pridam do slovniku
        output_json = dict()
        
        for span_tag in list(span_tags):
            if span_tag in SPAN_TAGS_TO_IGNORE:
                continue
            output_json[span_tag.text] = ""

        for span in self._spans:
            if(span.tag in SPAN_TAGS_TO_IGNORE):
                output_json[span.tag.text] = ""
                continue
            
            output_json[span.tag.text] = "".join([self.get_token_by_id(token_id).text for token_id in span.tokens]) 
            if span.tag == span_tags.PAYMENT_TYPE:
                output_json[span.tag.text] = " ".join([self.get_token_by_id(token_id).text for token_id in span.tokens]) 
    
        output_json.pop("vat", None)
        output_json.pop("vat_base", None)
        output_json.pop("vat_percentage", None)
        output_json.pop("o", None)
        
            

        return output_json


    #je totožná pro všechny faktury
    def to_json_layoutlmv3(self, img_path:str):

        span_tokens, span_boxes, span_tag_list, tokens, tokens_boxes, tokens_tag_list = self.intersect_tokens_tesseract(img_path)
        
        f_tokens, f_tokens_boxes, f_tokens_tag_list = [],[],[]
        f_span_tokens, f_span_boxes, f_span_tag_list = [],[],[]

        for tok, box, tag_id in zip(tokens, tokens_boxes, tokens_tag_list):
            tag = token_tags.from_id(tag_id)

            if(tag in TOKEN_TAGS_TO_IGNORE):
                tag_id = token_tags.O.code
            
            f_tokens.append(tok)
            f_tokens_boxes.append(box)
            f_tokens_tag_list.append(tag_id)

        for tok, box, tag_id in zip(span_tokens, span_boxes, span_tag_list):
            tag = span_tags.from_id(tag_id)          

            if(tag in SPAN_TAGS_TO_IGNORE or tag == span_tags.O):
                continue   
            
            f_span_tokens.append(tok)
            f_span_boxes.append(box)
            f_span_tag_list.append(tag_id)


        output = { 
                        "tokens":{  "tokens": f_tokens,
                                    "boxes": f_tokens_boxes,
                                    "tags":f_tokens_tag_list
                        },
                        "spans":{
                            "token_ids": f_span_tokens,
                            "boxes": f_span_boxes,
                            "tags": f_span_tag_list
                        }
        }

        return output  


    def to_json_coco(self, path_to_metadata_coco:str, img_name:str)->str:
        """
        path_to_metadata...cesta k metadata_coco.json, kvůli načtení dosavadních hodnot
        img_name...jméno obrázku pod kterým bude uložen...obrazek123456789.png
        vrátí dosavadní data obohacená o data této faktury
        """
        if not Path(path_to_metadata_coco).exists():
            with open(path_to_metadata_coco, mode="w") as f:
                f.write(json.dumps({
                "images":[],
                "annotations":[],
                "categories":[]
            }))

        with open(path_to_metadata_coco, "r+") as f:
            try:
                data = json.load(f)
            except:
                data = {"images":[], "annotations":[], "categories":[]}

            images = data.get("images", list())
            annotations = data.get("annotations", list())


            #filtrace spanů na základě bbox zda je na stránce a také tagu
            filtered = []
            w_img, h_img = self._A4_W_PX, self._A4_H_PX

            for span in self._spans:
                if(span.tag.code == 0 or span.tag in SPAN_TAGS_TO_IGNORE 
                
                or span.b_box[0] > w_img or span.b_box[2] > w_img 
                or span.b_box[0] < 0 or span.b_box[2] < 0

                or span.b_box[1] > h_img or span.b_box[2] > h_img
                or span.b_box[1] < 0 or span.b_box[2] < 0):
                
                    continue
                
                filtered.append((span.tokens, span.b_box, span.tag.code))  

            max_image_id = 0
            image_to_delte = None
            
            for image in images:
                if(image["file_name"] == img_name):
                    image_to_delte = image
                max_image_id = max(max_image_id, image["id"])

            

            if image_to_delte:
                annotations = [anno for anno in annotations if anno["image_id"] != image_to_delte["id"]]    
                images.remove(image_to_delte)
            

            _, spans_boxes, spans_tag_list = map(list, zip(*filtered)) if filtered else ([], [], [])
            
            for i, (box, tag) in enumerate(zip(spans_boxes, spans_tag_list)):
                # COCO vyžaduje [x_min, y_min, width, height] v pixelech
                x1, y1, x2, y2 = box
                width = x2 - x1
                height = y2 - y1 

                max_anno_id = 0 

                for anno in annotations:
                    max_anno_id = max(max_anno_id, anno["id"])
                
                ann = {
                    "id": max_anno_id+1,
                    "image_id": max_image_id+1,
                    "category_id": tag,
                    "bbox": [float(x1), float(y1), float(width), float(height)],
                    "area": float(width * height),
                    "iscrowd": 0,
                    "segmentation": [], # Pro detekci boxů stačí prázdné
                }
                annotations.append(ann)


            
            images.append({
                        "id": max_image_id+1,
                        "file_name": img_name,
                        "height": self._A4_H_PX,
                        "width": self._A4_W_PX,
                    })
            
            categories = [{"id": item.code, "name": item.text, "supercategory": None} for item in span_tags]

            output = {
                "images":images,
                "annotations":annotations,
                "categories":categories
            }

            return output

    def to_json_yolo(self)->str:
        #filtrace spanů na základě bbox zda je na stránce a také tagu
        filtered = []
        w_img, h_img = self._A4_W_PX, self._A4_H_PX

        for span in self._spans:
            if(span.tag.code == 0 or span.tag in SPAN_TAGS_TO_IGNORE
               or span.b_box[0] > w_img or span.b_box[2] > w_img 
               or span.b_box[0] < 0 or span.b_box[2] < 0

               or span.b_box[1] > h_img or span.b_box[2] > h_img
               or span.b_box[1] < 0 or span.b_box[2] < 0):
               
                continue
            
            filtered.append((span.tokens, span.b_box, span.tag.code))  


        _, spans_boxes, spans_tag_list = map(list, zip(*filtered)) if filtered else ([], [], [])

        yolo_str = ""

        for i, (box, tag) in enumerate(zip(spans_boxes, spans_tag_list)):            
            bbox_width = abs(box[2] - box[0])
            bbox_height = abs(box[3] - box[1])

            center_x = box[0] + bbox_width/2.0
            center_y = box[1] + bbox_height/2.0

            yolo_str += f'{tag} {center_x/w_img} {center_y/h_img} {bbox_width/w_img} {bbox_height/h_img} \n'
        
        return yolo_str
  
    #--------------------------------METODY EXPORTU FAKTUR ---------------------------------
    #----------------------------------------KONEC------------------------------------------

    #--------------------------------METODY IMPORTU FAKKTUR --------------------------------
    def from_layoutlmv3(self, layoutlmv3_path:Path, file_path:Path) -> bool:
        """
        Načte tokeny, spany a segmenty z layoutlmv3 souboru a podle jména faktury
        """

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
                        
                        self.append_token(GToken(None, text, box, tag_id, color))


                # --- načtení spanů ---

                spans = record["data"].get("spans", None)

                if spans:

                    sp_tokens = spans["token_ids"]#[[id prvního tokenu spanu 1, id druhého tokenu spanu 1], [id prvního tokenu spanu 2,...], [...], ...]
                    sp_tags = spans["tags"]
                    sp_boxes = spans["boxes"]
                    
                    for tokens_orig, tag_id, box in zip(sp_tokens, sp_tags, sp_boxes):
                        tokens = [self._tokens[token_orig_id].id for token_orig_id in tokens_orig]
                        self.append_span(GSpan(None, box, span_tags.from_id(tag_id), tokens,SET_SPAN_COLOR))


                # --- načtení segmentů ---
                segments = record["data"].get("segments", None)
                
                if segments:

                    seg_tags = segments["tags"]
                    seg_boxes = segments["boxes"]

                    for seg_id, box in zip(seg_tags, seg_boxes):
                        seg:segment_tags =  segment_tags.from_id(seg_id)
                        color = DEFAULT_SEGMENT_COLOR if seg_id == segment_tags.O else SET_SEGMENT_COLOR
                        
                        self.append_segment(GSegment(None, box, seg, color))

                return True
        return False
            
                


    #--------------------------------METODY IMPORTU FAKKTUR --------------------------------
    #----------------------------------------KONEC------------------------------------------

    #------------------------POMOCNÉ METODY -------------------------
    #--- práce se strukturami reprezentující informace na faktuře ---

    def alloc_span_id(self) -> int:
        i = self._next_span_id
        self._next_span_id += 1
        return i

    def alloc_token_id(self) -> int:
        i = self._next_token_id
        self._next_token_id += 1
        return i

    def alloc_relationship_id(self) -> int:
        i = self._next_relationship_id
        self._next_relationship_id += 1
        return i

    def alloc_segment_id(self) -> int:
        i = self._next_segment_id
        self._next_segment_id += 1
        return i
    
    def load_segments(self, segments:List[GSegment]) -> None:
        for segment in segments:
            self.append_segment(segment)
        
    def load_tokens(self, tokens:List[GToken]) -> None:
        for token in tokens:
            self.append_token(token)

    def load_spans(self, spans: List[GSpan]) -> None:
        for span in spans:
            self.append_span(span)
    
    #--- práce se strukturami reprezentující informace na faktuře ---
    #-----------------------------KONEC------------------------------
    
    #vrací bool na základě toho, zda je token obsažen již v některém z existujících spanů
    def is_in_spans(self, tok: GToken) -> bool:

        for span in self._spans:
            span_tokens: list[GToken] = [self.get_token_by_id(tok_index) for tok_index in span.tokens]
            
            if tok in span_tokens:
                return True

        return False

    def get_token_by_id(self, id:int) -> GToken|None:

        for tok in self._tokens:
            if(tok.id == id):
                return tok
            
        return None

    def get_span_by_id(self, id:int) -> GSpan|None:

        for span in self._spans:
            if(span.id == id):
                return span
            
        return None
    
    def get_relationship_by_id(self, id:int) -> GRelationship|None:

        for relationship in self._relationships:
            if(relationship.id == id):
                return relationship
            
        return None
    
    def get_segment_by_id(self, id:int) -> GSegment|None:

        for segment in self._segments:
            if(segment.id == id):
                return segment
            
        return None

    def get_span_by_containing_token(self, token:GToken) -> GSpan|None:

        for span in self._spans:
            if(token.id in span.tokens):
                return span
        
        return None

    def get_tokens_in_bounding_box(self, bbox:tuple[float, float, float, float]) -> List[GToken]:
        tokens_in: List[GToken] = list()
        
        for token in self._tokens:
            t_box = token.b_box

            if( (t_box[0] > bbox[0] and t_box[0] < bbox[2] and t_box[1] > bbox[1] and t_box[1] < bbox[3]) or #Levy horni
                (t_box[0] > bbox[0] and t_box[0] < bbox[2] and t_box[3] > bbox[1] and t_box[3] < bbox[3]) or #Levy spodni
                (t_box[2] > bbox[0] and t_box[2] < bbox[2] and t_box[3] > bbox[1] and t_box[3] < bbox[3]) or #Pravy dolni
                (t_box[2] > bbox[0] and t_box[2] < bbox[2] and t_box[1] > bbox[1] and t_box[1] < bbox[3]) #Pravy horni
                ):
                tokens_in.append(token) #alespon jeden roh bounding boxu tokenu je v boudning boux
                

        return tokens_in

    def append_token(self, tok: GToken) -> bool:
        if getattr(tok, "id", None) is None or getattr(tok, "id", -1) < 0:
            tok.id = self.alloc_token_id()
        
        self._tokens.append(tok)

        return True


    def append_span(self, span: GSpan) -> bool:
        # pokud span.id není přiděleno, přidělíme ho zde
        if getattr(span, "id", None) is None or getattr(span, "id", -1) < 0:
            span.id = self.alloc_span_id()

        for sp in self._spans:
            if (span.b_box == sp.b_box and span.tag == sp.tag and span.tokens == sp.tokens):
                print("Chyba. Span, který se snažíte přidat již na seznamu existuje.")
                return False
            if (span.id == sp.id):
                print("Chyba. Span s tímhle id již existuje.")
                return False

        self._spans.append(span)

        return True
    
    def append_relationship(self, relationship: GRelationship) -> bool:
        # pokud span.id není přiděleno, přidělíme ho zde
        if getattr(relationship, "id", None) is None or getattr(relationship, "id", -1) < 0:
            relationship.id = self.alloc_relationship_id()

        for rel in self._relationships:
            if (rel.span_a_index == relationship.span_a_index and rel.span_b_index == relationship.span_b_index):
                print("Chyba. Vztah, který se snažíte přidat již na seznamu existuje.")
                return False

        self._relationships.append(relationship)
        return True


    def append_segment(self, segment:GSegment) -> bool:
        
        if getattr(segment, "id", None) is None:
            segment.id = self.alloc_segment_id()

        for seg in self._segments:
            if (segment.b_box == seg.b_box and segment.tag == seg.tag):
                print("Chyba. Segment, který se snažíte přidat již na seznamu existuje.")
                return False
            if (segment.id == seg.id):
                print("Chyba. Segment s tímhle id již existuje.")
                return False
            
        self._segments.append(segment)
        return True

    def reset_token(self, token:GToken) -> bool:
        """ nastaví výchozí tag tokenu"""
        for tok in self._tokens:
            if(tok == token):
                tok.tag = token_tags.O
                tok.color = DEFAULT_TOKEN_COLOR
                
                return True
        return False
    
    def reset_tokens(self, *kwargs) -> bool:
        """ Odstraní všechny spany a nastaví výchozí tag všem tokenům"""
        for token in self._tokens:
            token.tag = token_tags.O
            token.color = DEFAULT_TOKEN_COLOR
        
        self.clear_spans()

        return True

    def remove_token(self, token:GToken) -> bool:
        if token in self._tokens:
            self._tokens.remove(token)
        else:
            return False
        
        #smažu spany, které obsahují ten token
        spans_to_delete = []
        for span in self._spans:
            for token_id in span.tokens:
                if(self.get_token_by_id(token_id) == None):
                    spans_to_delete.append(span)
                    break
        
        for span_to_delete in spans_to_delete:
            self.remove_span(span_to_delete)
    
        return True

    def remove_span(self, span:GSpan) -> bool:
        self._relationships = [
            rel for rel in self._relationships
            if rel.span_a != span and rel.span_b != span]

        if span in self._spans:
            self._spans.remove(span)
            
            return True
        
        return False

    def remove_relationship(self, relationship:GRelationship) -> bool:
        if relationship in self._relationships:
            self._relationships.remove(relationship)
            
            return True
        
        return False

    def remove_segment(self, segment: GSegment) -> bool:
        if segment in self._segments:
            self._segments.remove(segment)

            return True

        return False

    def clear_spans(self) -> None:
        self._spans = list()