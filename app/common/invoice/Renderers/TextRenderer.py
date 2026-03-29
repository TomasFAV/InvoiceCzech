import os
import random
from typing import Tuple
from PIL import ImageDraw
from PIL.ImageFont import FreeTypeFont
from common.invoice.models.GSpan import GSpan
from common.invoice.models.GToken import GToken
from common.enumerates.SpanTag import SpanTag
from common.enumerates.TokenTag import TokenTag
from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX, INK
from invoices_generator.utility.utils import load_font, mm, text_width
from common.invoice.models.Invoice import Invoice
from common.invoice.Renderers.InvoiceTextParaphraser import InvoiceTextParaphraser
from invoices_generator.utility.invoice_consts import fonts


class TextRenderer:

    def __init__(self):
        self.invoice_text_paraphraser:InvoiceTextParaphraser = InvoiceTextParaphraser()

        regular, bold = random.choice(fonts)
        self.font_regular_path = os.path.join("fonts", regular)
        self.font_bold_path = os.path.join("fonts", bold)

        # načteme všechny velikosti jen jednou

        self._f8 = load_font(self.font_regular_path, 8)
        self._f8b = load_font(self.font_bold_path, 8)
        self._f9 = load_font(self.font_regular_path, 9)
        self._f9b = load_font(self.font_bold_path, 9)
        self._f10 = load_font(self.font_regular_path, 10)
        self._f10b = load_font(self.font_bold_path, 10)
        self._f11 = load_font(self.font_regular_path, 11)
        self._f11b = load_font(self.font_bold_path, 11)
        self._f12 = load_font(self.font_regular_path, 12)
        self._f12b = load_font(self.font_bold_path, 12)
        self._f13 = load_font(self.font_regular_path, 13)
        self._f13b = load_font(self.font_bold_path, 13)
        self._f14 = load_font(self.font_regular_path, 14)
        self._f14b = load_font(self.font_bold_path, 14)
        self._f15 = load_font(self.font_regular_path, 15)
        self._f15b = load_font(self.font_bold_path, 15)
        self._f16 = load_font(self.font_regular_path, 16)
        self._f16b = load_font(self.font_bold_path, 16)
        self._f17 = load_font(self.font_regular_path, 17)
        self._f17b = load_font(self.font_bold_path, 17)
        self._f18 = load_font(self.font_regular_path, 18)
        self._f18b = load_font(self.font_bold_path, 18)
        self._f20b = load_font(self.font_bold_path, 20)
        self._f48b = load_font(self.font_bold_path, 48)


    #vrací dvojici x_souřadnice, kde vykreslovaný text končí
    #a index, který vypsaný span má
    def _text(self, invoice:Invoice, draw: ImageDraw.ImageDraw, poss: Tuple[float, float], text: str, font: FreeTypeFont, fill:Tuple[int, int, int],
            label:str|None = None, end:str|None = None, span_tag:SpanTag = SpanTag.O, must_have_same_width:bool = False) -> tuple[float, int|None]:
        
        
        #projdu jednotlive klice ve slovniku a pokusim se je najit v textu a zkusim je nahradit nahodnym synonymem ze slovniku --- kvuli lepsi generalizaci faktur
        text, font = self.invoice_text_paraphraser.paraphrase_and_fit(text,font, must_have_same_width)   


        x, y = poss
        span_index:int|None = None
        already_writen:str = ""

        if label is not None:
            #label bez tagu
            x, _ = self._text(invoice, draw, poss, text=label,font=font, fill=fill, span_tag=SpanTag.O)
        
        spans = [text]#víceslovný span
        if(span_tag == SpanTag.O):
            #v opačném případě je spanem slovo
            spans = text.split(" ")
        


        for index, sp in enumerate(spans):
            if not sp.strip():
                continue
            
            if(sp.replace(",","").replace(" ", "").isdecimal() and index+1<len(spans) and spans[index+1].replace(",","").replace(" ", "").isdecimal()):
                spans[index+1] = sp + spans[index+1]
                continue

            draw.text((x, y), str(sp), font=font, fill=fill)
            
            #rozměry spanu
            left, top, right, bottom = font.getbbox("ABCDEFGHIJKLMNOPQRSTUVWXYZ") #největší možná výška pro daný font
            span_width, span_height = text_width(sp,font), bottom - top + mm(0.75)


            ids:list[int] = list()

            if random.random() < 0.5:
                chunks = sp.split(" ")
            else:
                chunks = [sp]

            x_chunk = x
            for index, chunk in enumerate(chunks):
                already_writen += chunk
                if not chunk.strip():
                    continue

                token_tag:TokenTag = span_tag.ref

                if index != 0:
                    token_tag = token_tag.ref

                # relativní pozice
                chunk_width  = text_width(chunk,font)

                token_possition = ( (int)(x_chunk),
                            (int)(y - mm(0.75)),
                            (int)(x_chunk+chunk_width),
                            (int)(y+span_height))

                if (already_writen+" ") in sp:
                    chunk_width += text_width(" ", font)
                x_chunk += chunk_width

                ##MIMO STRÁNKU => nepřidám do ground-truth dat
                if(token_possition[0] >= _A4_W_PX or token_possition[1] >= _A4_H_PX 
                       or token_possition[2] >= _A4_W_PX or token_possition[3] >= _A4_H_PX):
                    continue
                

                ids.append(invoice._next_token_id)  # id tokenu
                invoice.append_token(GToken(None, chunk, token_possition, token_tag))

            span_possition = ((int)(x - mm(0.75)),
                            (int)(y - mm(0.75)),
                            (int)(x + span_width),
                            (int)(y + span_height))
            


            span_index = invoice._next_span_id
            invoice.append_span(GSpan(None,span_possition, tag=span_tag, tokens=ids))
            x += span_width + text_width("_", font)  #plus mezera mezi slovy



        if end is not None:
            #label bez tagu
            self._text(invoice, draw, (x, y), text=end, font=font, fill=fill, span_tag=SpanTag.O)
            x += text_width(end, font)

        return (x, span_index)


    def _text_right(self, invoice:Invoice, draw: ImageDraw.ImageDraw, x_right: float, y: float, text: str, font: FreeTypeFont, fill: tuple[int, int, int], span_tag: SpanTag = SpanTag.O,
    label: str | None = None, end: str | None = None, must_have_same_width:bool = False) -> tuple[float, int|None]:
        #vrací dvojici x_souřadnice, kde vykreslovaný text končí
        #a index, který vypsaný span má
        span_index:int|None = None

        parts = []
        if label:
            parts.append((label, SpanTag.O))   # label bez speciálního tagu
        parts.append((text, span_tag))           # hlavní text s tagem
        if end:
            parts.append((end, SpanTag.O))     # end taky bez tagu

        # celková šířka všech částí
        total_w = sum(text_width(t, font) for t, _ in parts)

        # začátek tak, aby to celé končilo na x_right
        x = x_right - total_w

        # vykreslí postupně všechny části
        for t, tg in parts:
            x, _ = self._text(invoice, draw, (x, y), text=t, font=font, fill=fill, span_tag=tg, must_have_same_width=must_have_same_width)
            if(tg != SpanTag.O):
                span_index = _

        return (x, span_index)

    def _text_center(self,invoice:Invoice, draw: ImageDraw.ImageDraw, x_center: float, y: float, text: str, font: FreeTypeFont, fill: tuple[int, int, int] = INK,
                    span_tag: SpanTag = SpanTag.O, label: str | None = None, end: str | None = None, must_have_same_width:bool = False) -> tuple[float, int|None]:
        #vrací dvojici x_souřadnice, kde vykreslovaný text končí
        #a index, který vypsaný span má
        span_index:int|None = None

        parts = []
        if label:
            parts.append((label+" ", SpanTag.O))   # label bez speciálního tagu
        parts.append((text, span_tag))           # hlavní text s tagem
        if end:
            parts.append((" "+end, SpanTag.O))     # end taky bez tagu

        # spočítat celkovou šířku
        total_w = sum(text_width(t, font) for t, _ in parts)

        # začátek tak, aby celek byl vycentrovaný
        x = x_center - total_w / 2

        # vykreslit všechny části za sebou
        for t, tg in parts:
            x, _ = self._text(invoice, draw, (x, y), t, font=font, fill=fill, span_tag=tg, must_have_same_width=must_have_same_width)
            if(tg != SpanTag.O):
                span_index = _

        return (x, span_index)