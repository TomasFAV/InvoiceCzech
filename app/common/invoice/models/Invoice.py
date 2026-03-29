from pathlib import Path
from common.invoice.models.GSegment import GSegment
from common.utils.GTesseract import GTesseract
from common.utils.consts import DEFAULT_TOKEN_COLOR

from common.invoice.models.GToken import GToken
from common.invoice.models.GSpan import GSpan


from PIL import Image
from PIL.ImageDraw import ImageDraw
from dataclasses import dataclass, field
from typing import List

from invoices_generator.utility.json_serializable import json_serializable
from common.enumerates.TokenTag import TokenTag


@dataclass
class Invoice(json_serializable):
    """
    Jedná se o třídu reprezentující fakturu, obsahuje tokeny, jimi tvořené spany a segmenty a také vyrenderovaný obrázek.
    Fakturu lze získat pouze rendererem, který přijimá data pro fakturu a template třídu
    Obsahuje metody pro práci s tokeny/spany/vztahy faktury
    """

    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################  

    tesseract:GTesseract = field(default_factory=GTesseract)

    ###############################################################
    #            Informace potřebné pro tvorbu datasetu           # 
    ###############################################################
    image:Image.Image = field(default_factory=Image.Image)

    _tokens:List[GToken] = field(default_factory=list)
    _spans:List[GSpan] = field(default_factory=list)
    _segments: List[GSegment] = field(default_factory=list)

    #alokace id
    _next_token_id:int = 0
    _next_span_id: int = 0
    _next_segment_id: int = 0
    
    ###############################################################
    #                            KONEC                            # 
    ###############################################################

            
    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################

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

    def get_tokens_in_area(self, area:tuple[float, float, float, float]) -> List[GToken]:
        tokens_in: List[GToken] = list()
        
        for token in self._tokens:
            t_box = token.b_box

            if( (t_box[0] > area[0] and t_box[0] < area[2] and t_box[1] > area[1] and t_box[1] < area[3]) or #Levy horni
                (t_box[0] > area[0] and t_box[0] < area[2] and t_box[3] > area[1] and t_box[3] < area[3]) or #Levy spodni
                (t_box[2] > area[0] and t_box[2] < area[2] and t_box[3] > area[1] and t_box[3] < area[3]) or #Pravy dolni
                (t_box[2] > area[0] and t_box[2] < area[2] and t_box[1] > area[1] and t_box[1] < area[3]) #Pravy horni
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
                tok.tag = TokenTag.O
                tok.color = DEFAULT_TOKEN_COLOR
                
                return True
        return False
    
    def reset_tokens(self, *kwargs) -> bool:
        """ Odstraní všechny spany a nastaví výchozí tag všem tokenům"""
        for token in self._tokens:
            token.tag = TokenTag.O
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
        if span in self._spans:
            self._spans.remove(span)
            
            return True
        
        return False

    def remove_segment(self, segment: GSegment) -> bool:
        if segment in self._segments:
            self._segments.remove(segment)

            return True

        return False

    def clear_tokens(self) -> None:
        self._tokens = list()

    def clear_spans(self) -> None:
        self._spans = list()

    def clear_segments(self) -> None:
        self._segments = list()

    def clear(self) -> None:
        self.clear_tokens()
        self.clear_spans()
        self.clear_segments()

    def remove_objects(self, area:tuple[int, int, int, int]) -> bool:
        """
            Odstraní tokeny a spany v dané oblasti
        """
        tokens_in_segments: List[GToken] = self.get_tokens_in_area(area)


        for token in tokens_in_segments:
            #najdu jestli je token v nějakém spanu
            span:GSpan = self.get_span_by_containing_token(token)
            if span is not None and self.image is not None:
                draw = ImageDraw(self.image)
                draw.rectangle(span.b_box, fill=(255,255,255))
                
            self.remove_token(token)
            self.remove_span(span)

        
    def load_image(self, img_path:Path):
        self.image = Image.open(img_path).convert("RGB")

    def save_image(self, img_path:Path):
        if not self.image:
            raise "Image not loaded"
        
        self.image.save(img_path, format="PNG")