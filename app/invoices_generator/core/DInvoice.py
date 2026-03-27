from collections import defaultdict
import json
from pathlib import Path
import re
from dataclasses import dataclass, field
import random
from typing import List, Tuple, Optional

from PIL import Image, ImageOps, ImageFilter, ImageDraw
from PIL.ImageFont import FreeTypeFont
import math
import os

import numpy as np

from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
from invoices_generator.core.enumerates.span_tags import SPAN_TAGS_TO_IGNORE, span_tags
from invoices_generator.core.bank import bank
from invoices_generator.core.company import company
from invoices_generator.core.enumerates.currency_code import currency_code
from invoices_generator.core.invoice_item import invoice_item
from invoices_generator.core.vat_item import vat_item
from invoices_generator.utility.invoice_consts import fonts
from invoices_generator.utility.json_serializable import json_serializable
from invoices_generator.core.enumerates.token_tags import token_tags

from invoices_generator.utility.utils import fit_line_bounding_box_font, fmt, fmt_money, mm, load_font, text_height, text_width
from invoices_generator.utility.invoice_consts import invoice_term_variants_expanded, invoice_term_variants
from invoices_generator.utility.invoice_consts import INK
from shared.Invoice import Invoice


@dataclass
class DInvoice(Invoice, json_serializable):
    """
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
    invoice_number: Optional[str] = ""
    variable_symbol: Optional[str] = ""
    bank_account_number: Optional[str] = ""
    IBAN:Optional[str] = ""
    const_symbol: Optional[str] = ""

    # datum vystavení
    issue_date: Optional[str] = ""
    # datum uskutečnění zdanitelného plnění
    taxable_supply_date: Optional[str] = ""
    # datum splatnosti
    due_date: Optional[str] = ""

    supplier: Optional[company] = field(default_factory=company)
    customer: Optional[company] = field(default_factory=company)

    rounding: Optional[float] = 0.0
    total_vat: Optional[float] = 0.0
    total_price: Optional[float] = 0.0 #s daní

    bank_account: Optional[bank] = field(default_factory=bank)
    payment_type: Optional[str] = "Apple pay"
    currency: Optional[currency_code] = currency_code.CZK
    

    description: Optional[str] = ""
    items: Optional[List[invoice_item]] = field(default_factory=list)
   

    ###############################################################
    #Grafické informace potřebné pro generování faktury do obrázku# 
    ###############################################################
    _DPI:int=200
    
    _A4_W_PX = int(round(8.27 * _DPI))  # 210 mm
    _A4_H_PX = int(round(11.69 * _DPI))  # 297 mm

    
    def __post_init__(self):
        # vybere se náhodná dvojice fontů při vytvoření instance
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

        for vat in vats:
            vat.vat = str(vat.vat)
            vat.vat_base = str(vat.vat_base)
            vat.vat_percentage = str(vat.vat_percentage)

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


    def to_json_donut(self, from_spans:bool = True, check_is_on_page:bool = True)->dict:
        if from_spans:
            """tvorba čistě na základě spanů a jejich ocr obsahu"""
            return super().to_json_donut()

        output_json = defaultdict(str)  
        temp_json = defaultdict(str)


        temp_json["invoice_number"] = fmt(str(self.invoice_number))
        temp_json["supp_register_id"] = fmt(str(self.supplier.register_id))
        temp_json["supp_tax_id"] = fmt(str(self.supplier.tax_id))
        temp_json["cust_register_id"] = fmt(str(self.customer.register_id)) 
        temp_json["cust_tax_id"] = fmt(str(self.customer.tax_id))
        temp_json["issue_date"] = fmt(str(self.issue_date))
        temp_json["taxable_supply_date"] = fmt(str(self.taxable_supply_date))
        temp_json["due_date"] = fmt(str(self.due_date))
        temp_json["payment_type"] = str(self.payment_type)
        temp_json["bank_account_number"] = fmt(str(self.bank_account_number))
        temp_json["iban"] = fmt(str(self.IBAN))
        temp_json["bic"] = fmt(str(self.bank_account.BIC))
        temp_json["variable_symbol"] = fmt(str(self.variable_symbol))
        temp_json["const_symbol"] = fmt(str(self.const_symbol))
        temp_json["total"] = fmt_money(self.total_price, False).replace('.',',')          

        if not check_is_on_page:
            return temp_json

        for span_tag in list(span_tags):
            if span_tag in SPAN_TAGS_TO_IGNORE or span_tag == span_tags.O:
                continue
            output_json[span_tag.text] = ""

        #zkontroluji, zda jsou na faktuře označeny
        for span in self._spans:
            if(span.tag in SPAN_TAGS_TO_IGNORE) or span.tag == span_tags.O:
                continue
            
            output_json[span.tag.text] = temp_json[span.tag.text]


        return output_json
    
    #--------------------------------METODY IMPORTU FAKKTUR --------------------------------
    def from_donut(self, donut_path: Path, file_path:Path) -> bool:
        
        """Načte json informace z donut souboru pro file_path fakturu"""

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


                self.invoice_number = data.get("invoice_number", "")
                
                self.supplier.register_id = data.get("supp_register_id", "")
                self.supplier.tax_id = data.get("supp_tax_id", "")

                self.customer.register_id = data.get("cust_register_id", "")
                self.customer.tax_id = data.get("cust_tax_id", "")

                self.issue_date = data.get("issue_date", "")
                self.taxable_supply_date = data.get("taxable_supply_date", "")
                self.due_date = data.get("due_date", "")

                self.payment_type = data.get("payment_type", "")
                self.bank_account_number = data.get("bank_account_number", "")
                self.bank_account.BIC = data.get("bic", "")
                self.IBAN = data.get("iban", "")
                self.variable_symbol = data.get("variable_symbol", "")
                self.const_symbol = data.get("const_symbol", "")
                self.total_price = data.get("total", "")        

                return True
        
        return False
    
    def from_dict(self, data:dict[str, str]):
        self.invoice_number = data.get("invoice_number", self.invoice_number)
        self.variable_symbol = data.get("variable_symbol", self.variable_symbol)
    
        self.const_symbol = data.get("const_symbol", self.const_symbol)
        self.issue_date = data.get("issue_date", self.issue_date)
        self.taxable_supply_date = data.get("taxable_supply_date", self.taxable_supply_date)
        self.due_date = data.get("due_date", self.due_date)
        self.total_price = data.get("total", self.total_price)
        self.IBAN = data.get("iban", self.IBAN)
        
        self.bank_account.BIC = data.get("bic", self.bank_account.BIC)

        self.supplier.register_id = data.get("supp_register_id", self.supplier.register_id)
        self.supplier.tax_id = data.get("supp_tax_id", self.supplier.tax_id)

        self.customer.register_id = data.get("cust_register_id", self.customer.register_id)
        self.customer.tax_id = data.get("cust_tax_id", self.customer.tax_id)

        self.payment_type = data.get("payment_type", self.payment_type)
        self.bank_account_number = data.get("bank_account_number", self.bank_account_number)

    def to_dict(self)->dict[str,str]:
        data:dict[str,str] = dict()
        
        data["invoice_number"] = self.invoice_number
        
        data["supp_register_id"] = self.supplier.register_id
        data["supp_tax_id"] = self.supplier.tax_id

        data["cust_register_id"] = self.customer.register_id
        data["cust_tax_id"] = self.customer.tax_id

        data["issue_date"] = self.issue_date
        data["taxable_supply_date"] = self.taxable_supply_date
        data["due_date"] = self.due_date

        data["payment_type"] = self.payment_type
        data["bank_account_number"] = self.bank_account_number

        data["iban"] = self.IBAN
        data["bic"] = self.bank_account.BIC

        data["variable_symbol"] = self.variable_symbol
        data["const_symbol"] = self.const_symbol
        
        data["total"] = self.total_price

        return data
    #--------------------------------METODY IMPORTU FAKKTUR --------------------------------
    #----------------------------------------KONEC------------------------------------------

    def generate_img(self, output_path:str)->bool:
        """
        Vykreslí obrázek faktury pomocí Pillow kreslících příkazů
        """

        return True
    
    def post_process(self, img: Image.Image) -> Image.Image:

        #return img
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
            img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.1, 0.5)))

        # --- přidání šumu (salt & pepper) ---
        if random.random() < 0.25:
            arr = np.array(img)
            amount = random.uniform(0.00005, 0.0002)  # 0.5–2 % pixelů
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

        #translace
        if random.random() < 1:
            a = 1
            b = 0
            c = random.random()*50 #left/right (i.e. 5/-5)
            d = 0
            e = 1
            f = random.random()*50 #up/down (i.e. 5/-5)
            img = img.transform(img.size, Image.AFFINE, (a, b, c, d, e, f), fillcolor=(255,255,255))
            self._apply_matrix(
            np.array([[1, b, -c],
                        [d,  1, -f],
                        [0,0,1]], float))


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

        for s in self._spans:
            left, top, right, bottom = s.b_box

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

            s.b_box = (n_left, n_top, n_right, n_bottom)

        for s in self._segments:
            left, top, right, bottom = s.b_box

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

            s.b_box = (n_left, n_top, n_right, n_bottom)


    def paraphrase_and_fit(self, original_text:str, font:FreeTypeFont, must_have_same_width:bool = False) -> tuple[str, FreeTypeFont]:
        """
        Vrací text, který má být vypsán a font, kterým má být daný text vypsán
        Plán hry:
        Zjistím jaký boundingbox by měl původní text
        Vyberu náhodně synonyma a pozměním text
        Upravím velikost fontu, tak aby zabíral nový text stejný prostor jako starý text
        Pokud velikost fontu klesne pod hranici čitelnosti, tj. například velikost 5, tak zkusím další synonymum
        Atd. dokud nenaleznu synonymum nebo nedojdou
        """
        original_txt_width, original_txt_height = text_width(original_text,font), text_height(original_text, font)

        if not must_have_same_width:
            return self.paraphrase(original_text), font
        
        new_text:str = self.paraphrase(original_text)
        new_font, new_font_size = fit_line_bounding_box_font(new_text, original_txt_width, font.path, min_font_size=15)
        
        while not new_font:
            new_text:str = self.paraphrase(original_text) #v nejhorším to poběží tak dlouho dokud to nevrátí samo sebe jako synonymum
            new_font, new_font_size = fit_line_bounding_box_font(new_text, original_txt_width, font.path, min_font_size=15)

        if new_font_size > font.size:
            new_font = font

        return new_text, new_font

    def paraphrase(self, original_text)->str:
        """Vrací originální text pozměněný o nějaká slova, která jsou synonymy nahrazených slov"""
        keys = sorted(invoice_term_variants_expanded.keys(), key=len, reverse=True)
        
        
        for key in keys:
            variants = invoice_term_variants_expanded[key]
        
            # regex – celé slovo / fráze, case-insensitive
            pattern = r"\b" + re.escape(key) + r"\b"

            new_text = re.sub(
                pattern,
                random.choice(variants),
                str(original_text),
                flags=re.IGNORECASE
            )

            if new_text != original_text:
                return new_text
        
        return new_text

    #vrací dvojici x_souřadnice, kde vykreslovaný text končí
    #a index, který vypsaný span má
    def _text(self, draw: ImageDraw.ImageDraw, poss: Tuple[float, float], text: str, font: FreeTypeFont, fill:Tuple[int, int, int],
            label:str|None = None, end:str|None = None, span_tag:span_tags = span_tags.O, must_have_same_width:bool = False) -> tuple[float, int|None]:
        
        
        #projdu jednotlive klice ve slovniku a pokusim se je najit v textu a zkusim je nahradit nahodnym synonymem ze slovniku --- kvuli lepsi generalizaci faktur
        text, font = self.paraphrase_and_fit(text,font, must_have_same_width)   


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

            draw.text((x, y), str(sp), font=font, fill=INK)
            
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

                token_tag:token_tags = span_tag.ref

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
                if(token_possition[0] >= self._A4_W_PX or token_possition[1] >= self._A4_H_PX 
                       or token_possition[2] >= self._A4_W_PX or token_possition[3] >= self._A4_H_PX):
                    continue
                

                ids.append(self._next_token_id)  # id tokenu
                self.append_token(GToken(None, chunk, token_possition, token_tag))

            span_possition = ((int)(x - mm(0.75)),
                            (int)(y - mm(0.75)),
                            (int)(x + span_width),
                            (int)(y + span_height))
            


            span_index = self._next_span_id
            self.append_span(GSpan(None,span_possition, tag=span_tag, tokens=ids))
            x += span_width + text_width("_", font)  #plus mezera mezi slovy



        if end is not None:
            #label bez tagu
            self._text(draw, (x, y), text=end, font=font, fill=fill, span_tag=span_tags.O)
            x += text_width(end, font)

        return (x, span_index)


    def _draw_right(self, draw: ImageDraw.ImageDraw, x_right: float, y: float, text: str, font: FreeTypeFont, fill: tuple[int, int, int], span_tag: span_tags = span_tags.O,
    label: str | None = None, end: str | None = None, must_have_same_width:bool = False) -> tuple[float, int|None]:
        #vrací dvojici x_souřadnice, kde vykreslovaný text končí
        #a index, který vypsaný span má
        span_index:int|None = None

        parts = []
        if label:
            parts.append((label, span_tags.O))   # label bez speciálního tagu
        parts.append((text, span_tag))           # hlavní text s tagem
        if end:
            parts.append((end, span_tags.O))     # end taky bez tagu

        # celková šířka všech částí
        total_w = sum(text_width(t, font) for t, _ in parts)

        # začátek tak, aby to celé končilo na x_right
        x = x_right - total_w

        # vykreslí postupně všechny části
        for t, tg in parts:
            x, _ = self._text(draw, (x, y), text=t, font=font, fill=fill, span_tag=tg, must_have_same_width=must_have_same_width)
            if(tg != span_tags.O):
                span_index = _

        return (x, span_index)

    def _draw_center(self, draw: ImageDraw.ImageDraw, x_center: float, y: float, text: str, font: FreeTypeFont, fill: tuple[int, int, int] = INK,
                    span_tag: span_tags = span_tags.O, label: str | None = None, end: str | None = None, must_have_same_width:bool = False) -> tuple[float, int|None]:
        #vrací dvojici x_souřadnice, kde vykreslovaný text končí
        #a index, který vypsaný span má
        span_index:int|None = None

        parts = []
        if label:
            parts.append((label+" ", span_tags.O))   # label bez speciálního tagu
        parts.append((text, span_tag))           # hlavní text s tagem
        if end:
            parts.append((" "+end, span_tags.O))     # end taky bez tagu

        # spočítat celkovou šířku
        total_w = sum(text_width(t, font) for t, _ in parts)

        # začátek tak, aby celek byl vycentrovaný
        x = x_center - total_w / 2

        # vykreslit všechny části za sebou
        for t, tg in parts:
            x, _ = self._text(draw, (x, y), t, font=font, fill=fill, span_tag=tg, must_have_same_width=must_have_same_width)
            if(tg != span_tags.O):
                span_index = _

        return (x, span_index)