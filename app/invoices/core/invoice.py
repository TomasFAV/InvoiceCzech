import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import random
from typing import Any, List

from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageEnhance
from PIL.ImageFont import FreeTypeFont, truetype
from decimal import Decimal, ROUND_HALF_UP
import math
import os

from jinja2 import Environment, FileSystemLoader
import numpy as np

from app.invoices.core.bank import bank
from app.invoices.core.company import company
from app.invoices.core.enumerates.currency_code import currency_code
from app.invoices.core.enumerates.payment_type import payment_type
from app.invoices.core.invoice_item import invoice_item
from app.invoices.core.vat_item import vat_item
from app.invoices.utility.invoice_consts import fonts
from app.invoices.utility.json_serializable import json_serializable


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
    #Grafické informace potřebné pro generování faktury do obrázku# 
    ###############################################################
    _DPI:int=100
    
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

    @abstractmethod
    def to_json(self)->Any:
        pass

    @abstractmethod
    def generate_img(self, output_path:str)->bool:
        """
        Vykreslí obrázek faktury pomocí Pillow kreslících příkazů
        """
        return True
    
    def post_process(self, img:Image.Image)->Image.Image:
        
        #náhodná rotace
        if random.random() < 0.2:  # 50% šance
            angle = random.randint(-15,15)
            img = img.rotate(angle, expand=True, fillcolor=(255, 255, 255),resample=Image.Resampling.BICUBIC)

        #náhodný grayscale
        if random.random() < 0.3:  # 30% šance
            img = ImageOps.grayscale(img).convert("RGB")

        # náhodný zoom (resize + oříznutí nebo přidání okrajů)
        if random.random() < 0.3:  # 30% šance
            zoom_factor = random.uniform(0.8, 1.1)  # 80% až 110%
            w, h = img.size
            img = img.resize((int(w * zoom_factor), int(h * zoom_factor)), Image.Resampling.LANCZOS)

            #pokud zmenšíme, vložíme do bílého plátna
            if zoom_factor < 1.0:
                new_img = Image.new("RGB", (w, h), (255, 255, 255))
                offset = ((w - img.size[0]) // 2, (h - img.size[1]) // 2)
                new_img.paste(img, offset)
                img = new_img
            else:
                # pokud je větší, ořízneme zpět na původní rozměr
                left = (img.size[0] - w) // 2
                top = (img.size[1] - h) // 2
                img = img.crop((left, top, left + w, top + h))

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


    def mm(self, x:float)->int:
        return int(round(x * self._DPI / 25.4))

    def _load_font(self, path:str, size:float, fallback:str="arial")->FreeTypeFont:
        SCALE:float = self._DPI/100.0 #přibližný a zjednodušený výpočet
        return truetype(path, size= size * SCALE)

    def _fmt_money(self, x:float)->str:
        try:
            return f"{Decimal(x).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}".replace(",", " ").replace(
                "\xa0", " ")
        except Exception:
            return str(x)

    def _text_width(self, draw: ImageDraw.ImageDraw, text: str, font: FreeTypeFont) -> float:
        return draw.textlength(text, font=font)

    def _draw_right(self, draw: ImageDraw.ImageDraw, x_right:float, y:float, text:str, font:FreeTypeFont, fill: tuple[int, int, int])->None:
        w = self._text_width(draw, text, font)
        draw.text((x_right - w, y), text, font=font, fill=fill)

    def _draw_center(self, draw: ImageDraw.ImageDraw, x_center:float, y:float, text:str, font:FreeTypeFont, fill:tuple[int, int, int])->None:
        w = self._text_width(draw, text, font)
        draw.text((x_center - w / 2, y), text, font=font, fill=fill)

    def _safe(self, val: Any, default:str="")->str:
        return "" if val is None else str(val)