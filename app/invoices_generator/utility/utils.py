from decimal import ROUND_HALF_UP, Decimal
from typing import Any, List
from PIL.ImageFont import FreeTypeFont, truetype
from PIL.ImageDraw import ImageDraw
from PIL import Image
import pytesseract
import random
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK


def get_rand_date():
    day = random.randint(1, 28)
    month = random.randint(1, 12)
    year = random.choice([2024, 2025, 2026])
    short_year = str(year)[2:]
            
    # Formáty: 01.02.2025, 1.2.2025, 01/02/25, 2025-02-01 atd.
    formats = [
        f"{day}.{month}.{year}",
        f"{day:02d}.{month:02d}.{year}",
        f"{day}/{month}/{year}",
        f"{day:02d}/{month:02d}/{short_year}",
        f"{year}-{month:02d}-{day:02d}",
        f"{day}. {month}. {year}",
    ]
    
    return random.choice(formats)

def safe(val: Any, default:str="")->str:
    return "" if val is None else str(val)

def fmt(x:str):
    """zformátuje pro json donut export"""
    return x.replace(" ", "")

def fmt_money(x: float, spaces:bool = True) -> str:
        try:
            # zaokrouhlení na dvě desetinná místa
            val = Decimal(x).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            s = f"{val:,.2f}"
            if spaces:
                s = s.replace(",", " ").replace(".", ",").replace("\xa0", " ")
            else:
                s = s.replace(",", "").replace(".", ",")
            return s
        except Exception:
            return str(x)


def get_item_value(item, field):
    if field in ["ppu", "price_with_vat"]: return fmt_money(getattr(item, field))
    if field == "vat_percentage": return f"{item.vat_percentage}%"
    return str(getattr(item, field))


def get_random_color():
    return (int(random.random()*255), int(random.random()*255), int(random.random()*255))

def get_random_style():
    """Generuje náhodné grafické prvky (rámečky, pozadí)."""
    return {
        "draw_border": random.random() > 0.7,
        "fill_bg": random.random() > 0.85,
        "line_width": random.choice([1, 2]),
        "border_type": random.choice(["full", "bottom", "left"])
    }

def draw_styled_rect(d, rect, style):
    """Vykreslí náhodný grafický podklad nebo ohraničení."""
    if style["fill_bg"]:
        d.rectangle(rect, fill=(245, 245, 245))
    if style["draw_border"]:
        if style["border_type"] == "full":
            d.rectangle(rect, outline=get_random_color(), width=style["line_width"])
        elif style["border_type"] == "bottom":
            d.line([(rect[0], rect[3]), (rect[2], rect[3])], fill=get_random_color(), width=style["line_width"])
        elif style["border_type"] == "left":
            d.line([(rect[0], rect[1]), (rect[0], rect[3])], fill=get_random_color(), width=style["line_width"] + 1)

def mm(x:float, DPI=200)->int:
    """Slouží pro převod pixelů na mm"""
    return int(round(x * DPI / 25.4))

def px(x:float, DPI=200)->int:
    """Slouží pro převod milimetrů na px"""
    return int(x/DPI*25.4)

def load_font(path:str, size:float, DPI=200, fallback:str="arial")->FreeTypeFont:
    SCALE:float = DPI/100.0 #přibližný a zjednodušený výpočet
    return truetype(path, size= size * SCALE)

def get_tesseract_words(img_path:str):
    """Získá slova a boxy z Tesseractu normalizované na 0-1000."""
    img = Image.open(img_path)
    w_img, h_img = img.size
        
    # Level 5 jsou jednotlivá slova
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
    tess_tokens = []
    tess_boxes = []
    tess_boxes_norm = []
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if text:
            # Normalizace souřadnic na 0-1000 pro LayoutLM
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            norm_box = [
                int(1000 * (x / w_img)),
                int(1000 * (y / h_img)),
                int(1000 * ((x + w) / w_img)),
                int(1000 * ((y + h) / h_img))
            ]

            tess_tokens.append(text)
            tess_boxes_norm.append(norm_box)
            tess_boxes.append([x,y, x+w, y+h])


    return tess_tokens, tess_boxes, tess_boxes_norm


def get_iou(boxA, boxB):
    """Vypočítá plochu průniku dvou boxů."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    inter_area = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    return inter_area 

def get_dimensions_symetry(boxA, boxB):
    """Vypočítá podobnost rozměrů bboxů"""
    widthA = abs(boxA[2] - boxA[0])
    widthB = abs(boxB[2] - boxB[0])

    heightA = abs(boxA[3] - boxA[0])
    heightB = abs(boxB[3] - boxB[0])

    max_width = max(widthA, widthB)
    max_height = max(heightA, heightB)

    min_width = min(widthA, widthB)
    min_height = min(heightA, heightB)

    if max_width == 0 or max_height == 0:
        return 0

    return  ((min_width/max_width) + (min_height/max_height))/(float(2)) 


# Příklad použití:
#boxy = [
#    [10, 10, 50, 50],
#    [60, 60, 100, 100],
#    [20, 5, 80, 70]
#]

def merge_bboxes(bboxes):
    if not bboxes:
        return None
    
    # Inicializace extrémních hodnot
    min_x = float('inf')
    min_y = float('inf')
    max_x = float('-inf')
    max_y = float('-inf')
    
    for x0, y0, x1, y1 in bboxes:
        if x0 < min_x: min_x = x0
        if y0 < min_y: min_y = y0
        if x1 > max_x: max_x = x1
        if y1 > max_y: max_y = y1
        
    return [min_x, min_y, max_x, max_y]

def text_width(text: str, font: FreeTypeFont) -> float:
    if not text:
       return 0.0
    left, top, right, bottom = font.getbbox(str(text))
    return right - left

def text_height(text: str, font:FreeTypeFont) -> float:
    if not text:
       return 0.0
    left, top, right, bottom = font.getbbox(str(text))
    return bottom - top


def fit_line_bounding_box_font(text:str, box_width:float, font_path:str="DejaVuSans.ttf", default_font_size = 30, min_font_size=10)->tuple[FreeTypeFont,int]:
        font_size = default_font_size
        font = truetype(font_path, font_size)
        while text_width(str(text), font) > box_width:
            font_size -= 1
            font = truetype(font_path, font_size)

            if font_size < min_font_size:
                return None, -1
            
        return font, font_size
    
def fit_text_bounding_box_font(words:List[str], box:tuple[float, float, float, float], font_path:str ="DejaVuSans.ttf", default_font_size = 30, min_font_size=10)->tuple[FreeTypeFont,int]:
    font_size = default_font_size
    font = truetype(font_path, font_size)
    box_width = box[2] - box[0]

    fit:bool = False
        
    x_end,y_end = box[2], box[3]
    space = 20

    while not fit:
        x,y = box[0], box[1]
        line_height, _ = font.getmetrics()
        space = max(space - 0.1, 0)

        for word in words:
            word_length:int = text_width(word, font)
            word_end_x = x + word_length
            if(word_end_x > x_end):
                x = box[0]
                y += line_height + space
                
            x = x + word_length + text_width(" ", font)
            
            #jelikož začínáme z levého horního rohu, tak odečítáme line_height
        fit = x < x_end and y < y_end - line_height
        if fit:
            return font, font_size, space
                
        font_size = font_size - 1
        font = truetype(font_path, font_size)     
            
        if font_size < min_font_size:
            return None, -1, -1