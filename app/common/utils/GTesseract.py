from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import sys
from PIL import Image
import pytesseract
from pytesseract import Output


@dataclass
class TesseractConfig:
    language:str = "ces"
    tesseract_exe_path:str = ""


class GTesseract:
    """
    Wrapper pro práci s knihovnou pytesseract
    """
    
    def __init__(self, config:TesseractConfig = TesseractConfig()):
        self.config = config
        self.__config__tesseract()

        pass


    def __config__tesseract(self):
        
        candidates = []

        #PATH (funguje na všech OS)
        path = shutil.which("tesseract")
        if path:
            candidates.append(path)

        #ENV proměnná (uživatel si může nastavit vlastní cestu)
        env_path = os.getenv("TESSERACT_CMD")
        if env_path:
            candidates.append(env_path)

        #OS specifické fallbacky
        if sys.platform == "win32":
            candidates.extend([
                r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            ])
        elif sys.platform.startswith("linux"):
            candidates.extend([
                "/usr/bin/tesseract",
                "/usr/local/bin/tesseract",
            ])
        elif sys.platform == "darwin":  # macOS
            candidates.extend([
                "/opt/homebrew/bin/tesseract",
                "/usr/local/bin/tesseract",
            ])

        #Najdi první existující
        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                pytesseract.pytesseract.tesseract_cmd = candidate
                return

        raise RuntimeError(
            "Tesseract OCR nebyl nalezen.\n"
            "Řešení:\n"
            "- nainstaluj Tesseract\n"
            "- nebo ho přidej do PATH\n"
            "- nebo nastav TESSERACT_CMD"
        )
        

    def extract_text(self, img_path:Path, min_confidence:int = 30) -> tuple[list[str], list[tuple[int, int, int, int]], list[tuple[int, int, int, int]]]:               
        image = Image.open(img_path)
        data = pytesseract.image_to_data(image, lang=self.config.language, output_type=Output.DICT)
        
        bbox = [((int)(l),(int)(t),(int)((l+w)),(int)((t+h)))  for l,t,w,h,c in zip(data["left"], data["top"], data["width"], data["height"], data["conf"]) if c != -1 and c > min_confidence]
        bbox_norm = [((int)(1000*((float)(l)/image.width)),(int)(1000*((float)(t)/image.height)),(int)(1000*((float)(l+w)/image.width)),(int)(1000*((float)(t+h)/image.height)))  for l,t,w,h,c in zip(data["left"], data["top"], data["width"], data["height"], data["conf"]) if c != -1 and c > min_confidence]
        text = [t  for t,c in zip(data["text"], data["conf"]) if c != -1 and c > min_confidence]

        return text, bbox, bbox_norm
    
    def extract_text_from_image(self, image:Image.Image, min_confidence:int = 30) -> tuple[list[str], list[tuple[int, int, int, int]], list[tuple[int, int, int, int]]]:               
        data = pytesseract.image_to_data(image, lang=self.config.language, output_type=Output.DICT)
        
        bbox = [((int)(l),(int)(t),(int)((l+w)),(int)((t+h)))  for l,t,w,h,c in zip(data["left"], data["top"], data["width"], data["height"], data["conf"]) if c != -1 and c > min_confidence]
        bbox_norm = [((int)(1000*((float)(l)/image.width)),(int)(1000*((float)(t)/image.height)),(int)(1000*((float)(l+w)/image.width)),(int)(1000*((float)(t+h)/image.height)))  for l,t,w,h,c in zip(data["left"], data["top"], data["width"], data["height"], data["conf"]) if c != -1 and c > min_confidence]
        text = [t  for t,c in zip(data["text"], data["conf"]) if c != -1 and c > min_confidence]

        return text, bbox, bbox_norm