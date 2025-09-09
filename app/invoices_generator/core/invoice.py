from itertools import islice
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import random
from typing import Any, List, Tuple

from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageEnhance
from PIL.ImageFont import FreeTypeFont, truetype
from decimal import Decimal, ROUND_HALF_UP
import math
import os

from jinja2 import Environment, FileSystemLoader
import numpy as np
import pytesseract
from pytesseract import Output

from app.ie_engine.enumerates.engines import engines
from app.invoices_generator.core.bank import bank
from app.invoices_generator.core.company import company
from app.invoices_generator.core.enumerates.currency_code import currency_code
from app.invoices_generator.core.enumerates.payment_type import payment_type
from app.invoices_generator.core.enumerates.span_tags import span_tags
from app.invoices_generator.core.invoice_item import invoice_item
from app.invoices_generator.core.relationship import relationship
from app.invoices_generator.core.vat_item import vat_item
from app.invoices_generator.core.token import token
from app.invoices_generator.utility.invoice_consts import fonts
from app.invoices_generator.utility.json_serializable import json_serializable
from app.invoices_generator.core.enumerates.token_tags import token_tags
from app.invoices_generator.core.span import span


@dataclass
class invoice(json_serializable, ABC):
    """
    Abstraktní třída faktury.

    :param invoice_number: Číslo faktury
    :param variable_symbol: Variabilní symbol (např. pro platbu)
    :param const_symbol: Konstantní symbol
    :param description: Textový popis faktury

    :param issue_date: Datum vystavení faktury
    :param taxable_supply_date: Datum uskutečnění zdanitelného plnění
    :param due_date: Datum splatnosti

    :param supplier: Dodavatel (firma, která fakturu vystavuje)
    :param customer: Odběratel (firma, která fakturu přijímá)

    :param rounding: Hodnota zaokrouhlení
    :param total_vat: Celková částka DPH (lze přepočítat z položek)
    :param total_price: Celková cena včetně DPH (lze přepočítat z položek)

    :param bank_account: Bankovní účet dodavatele
    :param payment: Typ platby (např. převodem, hotově, kartou)
    :param currency: Měna faktury (default CZK)

    :param items: Seznam položek faktury (`invoice_item`)
    :param vat: Seznam ďanových položek faktury (`vat_item`)
    """

    ############################
    ####                    ####
    ####     PROPERTIES     ####
    ####                    ####
    ############################
    invoice_number: str
    variable_symbol: str
    bank_account_number: str
    IBAN:str
    const_symbol: str

    # datum vystavení
    issue_date: str
    # datum uskutečnění zdanitelného plnění
    taxable_supply_date: str
    # datum splatnosti
    due_date: str

    supplier: company
    customer: company

    rounding: float
    total_vat: float
    total_price: float #s daní

    bank_account: bank
    payment: payment_type
    currency: currency_code = currency_code.CZK
    

    description: str = ""
    items: List[invoice_item] = field(default_factory=list)

    ###############################################################
    #            Informace potřebné pro tvorbu datasetu           # 
    ###############################################################

    _tokens:List[token] = field(default_factory=list)
    _spans:List[span] = field(default_factory=list)
    _relationships: List[relationship] = field(default_factory=list)

    ###############################################################
    #Grafické informace potřebné pro generování faktury do obrázku# 
    ###############################################################
    _DPI:int=200
    
    _A4_W_PX = int(round(8.27 * _DPI))  # 210 mm
    _A4_H_PX = int(round(11.69 * _DPI))  # 297 mm

    # Barvy
    _INK = (17, 17, 17)
    _MUTED = (88, 88, 88)
    _LINE = (214, 214, 214)
    _LINE_MID = (169, 169, 169)
    _LINE_STRONG = (0, 0, 0)
    _BG = (255, 255, 255)
    _SUBTLE_BG = (250, 250, 250)
    _FOOT_BG = (251, 251, 251)
    _BOX_BG = (252, 252, 252)
    _TMOBILE_PINK = (226, 0, 126)

    def __post_init__(self):
        # vybere se náhodná dvojice fontů při vytvoření instance
        regular, bold = random.choice(fonts)
        self.font_regular_path = os.path.join("fonts", regular)
        self.font_bold_path = os.path.join("fonts", bold)

        # načteme všechny velikosti jen jednou

        self._f8 = self._load_font(self.font_regular_path, 8)
        self._f8b = self._load_font(self.font_bold_path, 8)
        self._f9 = self._load_font(self.font_regular_path, 9)
        self._f9b = self._load_font(self.font_bold_path, 9)
        self._f10 = self._load_font(self.font_regular_path, 10)
        self._f10b = self._load_font(self.font_bold_path, 10)
        self._f11 = self._load_font(self.font_regular_path, 11)
        self._f11b = self._load_font(self.font_bold_path, 11)
        self._f12 = self._load_font(self.font_regular_path, 12)
        self._f12b = self._load_font(self.font_bold_path, 12)
        self._f13b = self._load_font(self.font_bold_path, 13)
        self._f14 = self._load_font(self.font_regular_path, 14)
        self._f14b = self._load_font(self.font_bold_path, 14)
        self._f16 = self._load_font(self.font_regular_path, 16)
        self._f16b = self._load_font(self.font_bold_path, 16)
        self._f17b = self._load_font(self.font_bold_path, 17)
        self._f17b = self._load_font(self.font_bold_path, 17)
        self._f18b = self._load_font(self.font_bold_path, 18)
        self._f20b = self._load_font(self.font_bold_path, 20)
        self._f48b = self._load_font(self.font_bold_path, 48)

    ###############################################################
    #                            KONEC                            # 
    ###############################################################

    @property
    def vat(self) -> List[vat_item]:

        vats: List[vat_item] = list()

        for item in self.items:
            found = False

            for vat in vats:
                if (item.vat_percentage == vat.vat_percentage):
                    vat.vat_base += item.price_without_vat
                    vat.vat += item.vat
                    found = True

                    break

            if not found:
                vat = vat_item(item.vat_percentage, item.price_without_vat, item.vat)
                vats.append(vat)

        return vats

    @property
    def calculated_total_price(self) -> float:
        price:float = 0
        for item in self.items:
            price += item.price_with_vat
        return round(price,2)

    @property
    def calculated_total_vat(self) -> float:
        vat:float = 0
        for item in self.items:
            vat += item.vat
        return round(vat,2)

    @property
    def calculated_total_price_without_vat(self) -> float:
        return round(self.calculated_total_price - self.calculated_total_vat,2)

    ############################
    ####                    ####
    ####       METHODS      ####
    ####                    ####
    ############################

    def generate_html(self, template_path: str, output_path: str) -> bool:
        env = Environment(loader=FileSystemLoader("app/invoices/templates"))
        tpl = env.get_template(template_path)

        html = tpl.render(invoice=self, now=datetime.now().strftime("%d.%m.%Y %H:%M"))
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return True

    def to_json(self, img_path:str,engine:engines = engines.DONUT)->Any:
        if(engine == engines.DONUT):
            return self.to_json_donut()
        elif(engine == engines.LAYOUTLMv3):
            return self.to_json_layoutlmv2(img_path)

    def extract_words_teseract(self, img_path:str)->None:
        lang = "ces"  # jazykové balíčky Tesseractu musí být nainstalované (ces.traineddata)

        pytesseract.pytesseract.tesseract_cmd = r'E:\user\plocha\BP\packages\tesseract.exe'
        data = pytesseract.image_to_data(Image.open(img_path), lang=lang, output_type=Output.DICT)
        print(data)

        lines = []
        n = len(data["text"])
        for i in range(n):
            text = data["text"][i]
            conf = float(data["conf"][i]) if data["conf"][i] != "-1" else 0.0
            if not text.strip():
                continue

            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            box = (x, y, x+w, y+h)
            lines.append({"box": box, "text": text, "conf": conf})

        # 3) vykreslení do kopie
        out = Image.open(img_path)
        draw = ImageDraw.Draw(out)
        font = self._f10
        for index, ln in enumerate(lines):
            if ln["conf"] < 20:  # tesseract confidence je 0–100
                continue
            draw.rectangle(ln["box"], outline="red", width=2)
            x, y = ln["box"][0], ln["box"][1]
            draw.text((x, max(0, y-12)), f'{ln["text"]} ({ln["conf"]:.1f})',
                    font=font, fill="red")

        out.show()

        pass

    

    @abstractmethod
    def to_json_donut(self)->str:
        pass

    #je totožná pro všechny faktury
    def to_json_layoutlmv2(self, img_path:str)->str:
        tokens, tokens_boxes, tokens_tag_list = ([], [], []) if not self._tokens else map(list, zip(*((w.text, w.b_box, w.tag.code) for w in self._tokens)))
        spans_tokens_indices, spans_boxes, spans_tag_list = ([], [], []) if not self._spans else map(list, zip(*((w.tokens, w.b_box, w.tag.code) for w in self._spans)))
        spans_a_indices, spans_b_indices, relationship_types = ([], [], []) if not self._relationships else map(list, zip(*((w.span_a_index, w.span_b_index, w.type.code) for w in self._relationships)))

        output = { 
                        "tokens":{  "tokens": tokens,
                                    "boxes": tokens_boxes,
                                    "tags":tokens_tag_list
                        },
                        "spans":{
                                    "token_indices":spans_tokens_indices,
                                    "boxes": spans_boxes,
                                    "tags": spans_tag_list        
                        },
                        "relationships":{
                                    "span_index_a":spans_a_indices,
                                    "span_index_b":spans_b_indices,
                                    "relationship_type":relationship_types
                        }
        }
        
        return output

    @abstractmethod
    def generate_img(self, output_path:str)->bool:
        """
        Vykreslí obrázek faktury pomocí Pillow kreslících příkazů
        """
        return True
    
    def post_process(self, img: Image.Image) -> Image.Image:

        return img
        # náhodná rotace (40 %)
        if random.random() < 0.4:
            angle_deg = random.randint(-2, 2)

            #rozměry plátna před rotatcí
            w, h = img.size
            img = img.rotate(angle_deg, expand=True, fillcolor=(255,255,255),
                            resample=Image.Resampling.BICUBIC)

            #střed plátna
            cx, cy = w/2.0, h/2.0
            θ = math.radians(-angle_deg)

            T1 = np.array([[1,0,-cx],[0,1,-cy],[0,0,1]], float)
            R  = np.array([[math.cos(θ), -math.sin(θ), 0],
                        [math.sin(θ),  math.cos(θ), 0],
                        [0,0,1]], float)
            T2c = np.array([[1,0,cx],[0,1,cy],[0,0,1]], float)

            #rotace podle středu plátna
            M_center = T2c @ R @ T1

            #kvůli EXPANZI...spočítám kam se transformovali rohové body
            corners = np.array([[0,   w,   w,   0],
                                [0,   0,   h,   h],
                                [1,   1,   1,   1]], float) #[roh 1, roh2, roh3, roh4]
            tc = M_center @ corners #(3,3)*(3,4) = (3,4)...[t-roh1, t-roh2, t-roh3, t-roh4]
            ox = -tc[0,:].min()
            oy = -tc[1,:].min()

            Toffset = np.array([[1,0,ox],[0,1,oy],[0,0,1]], float)
            M = Toffset @ M_center

            self._apply_matrix(M)  # → uvnitř transformuj 4 rohy každého bboxu

            w, h = img.size
            
            #downscale zvětšeného plátna
            scale_w, scale_h = float(self._A4_W_PX)/w, float(self._A4_H_PX)/h 

            S = np.array([[scale_w, 0, 0],
                        [0,  scale_h, 0],
                        [0,0,1]], float)

            self._apply_matrix(S)  # → uvnitř transformuj 4 rohy každého bboxu

            img = img.resize((self._A4_W_PX,self._A4_H_PX),resample=Image.Resampling.BICUBIC)

        #náhodný grayscale
        if random.random() < 0.3:  # 30% šance
            img = ImageOps.grayscale(img).convert("RGB")

        # --- Gaussian blur (efekt naskenovaného papíru) ---
        if random.random() < 0.3:
            img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.5, 1.5)))

        # --- přidání šumu (salt & pepper) ---
        if random.random() < 0.3:
            arr = np.array(img)
            amount = random.uniform(0.005, 0.02)  # 0.5–2 % pixelů
            noise = np.random.choice([0, 255], arr.shape, p=[1 - amount, amount]).astype(np.uint8)
            mask = np.random.rand(*arr.shape[:2]) < amount
            arr[mask] = noise[mask]
            img = Image.fromarray(arr)

        # --- zažloutlý papír ---
        if random.random() < 0.25:
            overlay = Image.new("RGB", img.size, (240, 230, 200))
            img = Image.blend(img, overlay, 0.08)

        # --- náhodné čáry (škrábance, stopy skeneru) ---
        if random.random() < 0.2:
            d = ImageDraw.Draw(img)
            for _ in range(random.randint(1, 3)):
                x1, y1 = random.randint(0, img.width), random.randint(0, img.height)
                x2, y2 = random.randint(0, img.width), random.randint(0, img.height)
                d.line((x1, y1, x2, y2), fill=(150, 150, 150), width=random.randint(1, 3))

        if random.random() < 0.3:  # 30% šance
            img = ImageOps.grayscale(img).convert("RGB")

        return img


    def _apply_matrix(self, M: np.ndarray):
        """
        Správně transformuje všech 4 rohy b-boxu homogenní maticí M.
        """
        for w in self._tokens:
            left, top, right, bottom = w.b_box

            # čtyři rohy v homogenních souřadnicích
            pts = np.array([
                [left,  top,    1.0],
                [right, top,    1.0],
                [right, bottom, 1.0],
                [left,  bottom, 1.0],
            ], dtype=float).T  #(3,4)

            # transformované body 
            tpts = (M @ pts)  #(3,4)

            xs = tpts[0, :]
            ys = tpts[1, :]

            n_left   = float(xs.min())
            n_right  = float(xs.max())
            n_top    = float(ys.min())
            n_bottom = float(ys.max())

            w.b_box = (n_left, n_top, n_right, n_bottom)




    def mm(self, x:float)->int:
        return int(round(x * self._DPI / 25.4))

    def _load_font(self, path:str, size:float, fallback:str="arial")->FreeTypeFont:
        SCALE:float = self._DPI/100.0 #přibližný a zjednodušený výpočet
        return truetype(path, size= size * SCALE)

    def _fmt_money(self, x: float) -> str:
        try:
            # zaokrouhlení na dvě desetinná místa
            val = Decimal(x).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            s = f"{val:,.2f}"
            s = s.replace(",", " ").replace(".", ",").replace("\xa0", " ")
            return s
        except Exception:
            return str(x)


    def _text(self, draw: ImageDraw.ImageDraw, poss: Tuple[float, float], text: str, font: FreeTypeFont, fill:Tuple[int, int, int],
            label:str|None = None, end:str|None = None, span_tag:span_tags = span_tags.O, hard_undersampling:bool = True) -> tuple[float, int|None]:
        
        #vrací dvojici x_souřadnice, kde vykreslovaný text končí
        #a index, který vypsaný span má

        x, y = poss
        span_index:int|None = None
        already_writen:str = ""

        if label is not None:
            #label bez tagu
            x, _ = self._text(draw, poss, text=label,font=font, fill=fill, span_tag=span_tags.O)
        
        spans = [text]#víceslovný span
        if(span_tag == span_tags.O):
            #v opačném případě je spanem slovo
            spans = text.split(" ")
        


        for index, sp in enumerate(spans):
            if not sp.strip():
                continue
            
            if(sp.replace(",","").replace(" ", "").isdecimal() and index+1<len(spans) and spans[index+1].replace(",","").replace(" ", "").isdecimal()):
                spans[index+1] = sp + spans[index+1]
                continue

            draw.text((x, y), str(sp), font=font, fill=self._INK)
            
            #rozměry spanu
            left, top, right, bottom = font.getbbox("ABCDEFGHIJKLMNOPQRSTUVWXYZ") #největší možná výška pro daný font
            span_width, span_height = self._text_width(draw,sp,font), bottom - top + self.mm(0.75)


            indices:list[int] = list()
            chunks = sp.split(" ")

            if random.random() < 0.3:
                chunks = self._random_chunk(chunks)
        
            x_chunk = x
            for index, chunk in enumerate(chunks):
                already_writen += chunk
                if not chunk.strip():
                    continue

                token_tag:token_tags = span_tag.ref

                if index != 0:
                    token_tag = token_tag.ref

                # relativní pozice
                chunk_width  = self._text_width(draw,chunk,font)


                token_possition = ((x_chunk)/self._A4_W_PX,
                            (y - self.mm(0.75))/self._A4_H_PX,
                            (x_chunk+chunk_width)/self._A4_W_PX,
                            (y+span_height)/self._A4_H_PX)

                if (already_writen+" ") in sp:
                    chunk_width += self._text_width(draw, " ", font)
                x_chunk += chunk_width

                ##UNDERSAMPLING
                ##HARD UNDERSAMPLING
                if(span_tag == span_tags.O and hard_undersampling and random.choice([True,False, False, False, False, False, False])):
                    indices.append(len(self._tokens)) #index tokenu
                    self._tokens.append(token(chunk,token_possition,token_tag))
                ##SOFT UNDERSAMPLING
                if(span_tag == span_tags.O and not hard_undersampling and random.choice([True, True, True, True, False, False, False])):
                    indices.append(len(self._tokens)) #index tokenu
                    self._tokens.append(token(chunk,token_possition,token_tag))

                if(span_tag != span_tags.O):
                    indices.append(len(self._tokens)) #index tokenu
                    self._tokens.append(token(chunk,token_possition,token_tag))

            span_possition = (((x - self.mm(0.75)/self._A4_W_PX)*1000),
                            ((y - self.mm(0.75)/self._A4_H_PX))*1000,
                            ((x+span_width)/self._A4_W_PX)*1000,
                            ((y+span_height)/self._A4_H_PX)*1000)

            if(span_tag != span_tags.O):
                span_index = len(self._spans)
                self._spans.append(span(span_possition,tag=span_tag, tokens=indices))    
            x += span_width + self._text_width(draw, "_", font)  #plus mezera mezi slovy

        if end is not None:
            #label bez tagu
            self._text(draw, (x, y), text=end, font=font, fill=fill, span_tag=span_tags.O)
            x += self._text_width(draw, end, font)

        return (x, span_index)

    def _text_width(self, draw: ImageDraw.ImageDraw, text: str, font: FreeTypeFont) -> float:
        if not text:
            return 0.0
        left, top, right, bottom = font.getbbox(text)
        return right - left

    def _draw_right(self, draw: ImageDraw.ImageDraw, x_right: float, y: float, text: str, font: FreeTypeFont, fill: tuple[int, int, int], tag: span_tags = span_tags.O,
    label: str | None = None, end: str | None = None, undersampling:bool = True) -> tuple[float, int|None]:
        #vrací dvojici x_souřadnice, kde vykreslovaný text končí
        #a index, který vypsaný span má
        span_index:int|None = None

        parts = []
        if label:
            parts.append((label, span_tags.O))   # label bez speciálního tagu
        parts.append((text, tag))           # hlavní text s tagem
        if end:
            parts.append((end, span_tags.O))     # end taky bez tagu

        # celková šířka všech částí
        total_w = sum(self._text_width(draw, t, font) for t, _ in parts)

        # začátek tak, aby to celé končilo na x_right
        x = x_right - total_w

        # vykreslí postupně všechny části
        for t, tg in parts:
            x, _ = self._text(draw, (x, y), text=t, font=font, fill=fill, span_tag=tg, hard_undersampling=undersampling)
            if(tg != span_tags.O):
                span_index = _

        return (x, span_index)

    def _draw_center(self, draw: ImageDraw.ImageDraw, x_center: float, y: float, text: str, font: FreeTypeFont, fill: tuple[int, int, int] = _INK,
                    tag: span_tags = span_tags.O, label: str | None = None, end: str | None = None, undersampling:bool = True) -> tuple[float, int|None]:
        #vrací dvojici x_souřadnice, kde vykreslovaný text končí
        #a index, který vypsaný span má
        span_index:int|None = None

        parts = []
        if label:
            parts.append((label+" ", span_tags.O))   # label bez speciálního tagu
        parts.append((text, tag))           # hlavní text s tagem
        if end:
            parts.append((" "+end, span_tags.O))     # end taky bez tagu

        # spočítat celkovou šířku
        total_w = sum(self._text_width(draw, t, font) for t, _ in parts)

        # začátek tak, aby celek byl vycentrovaný
        x = x_center - total_w / 2

        # vykreslit všechny části za sebou
        for t, tg in parts:
            x, _ = self._text(draw, (x, y), t, font=font, fill=fill, span_tag=tg, hard_undersampling=undersampling)
            if(tg != span_tags.O):
                span_index = _

        return (x, span_index)

    def _safe(self, val: Any, default:str="")->str:
        return "" if val is None else str(val)
    
    def _random_chunk(self, text:list[str], min_chunk=3, max_chunk=5):
        #nefunguje tak jak by člověk očekával, ale funguje dobře
        tokens:list[str] = list()
        
        for chunk in text:

            index = 0

            while index < len(chunk):
                
                limit = index+max_chunk

                end_index = index + random.randint(min_chunk, max_chunk)
                
                if(end_index>len(chunk)):
                    end_index = len(chunk)

                tokens.append(chunk[index:end_index])

                index = end_index

        return tokens