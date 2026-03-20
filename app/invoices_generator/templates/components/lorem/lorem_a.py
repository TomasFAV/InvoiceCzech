from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money


class lorem_a(invoice_component):

    def __init__(self):
        pass

    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        # Respektujeme zadanou šířku, defaultně mm(100)
        width = kwargs.get("width", mm(85))
        start_y = y

        # 1. Grafická vata: Simulace QR kódu
        # QR kód zarovnáme k pravému okraji definované šířky
        qr_size = mm(18)
        qr_x = x + width - qr_size
        
        d.rectangle([qr_x, y, qr_x + qr_size, y + qr_size], outline=LINE_MID, width=1)
        # Simulace obsahu QR
        for _ in range(35):
            dot_x = qr_x + random.randint(1, int(qr_size - 3))
            dot_y = y + random.randint(1, int(qr_size - 3))
            d.rectangle([dot_x, dot_y, dot_x + 2, dot_y + 2], fill=INK)
        
        inv._text(d, (qr_x, y + qr_size + mm(1)), text="QR PLATBA / INFO", font=inv._f8b, fill=MUTED)

        # 2. Marketingový slogan
        # Omezíme šířku sloganu, aby nenarazil do QR kódu
        inv._text(d, (x, y), text="DĚKUJEME ZA VAŠI DŮVĚRU!", font=inv._f10b, fill=TMOBILE_PINK)
        y += mm(7)

        # 3. Právní vata se zalamováním (Word Wrap)
        lorem_phrases = [
            "Platba se považuje za uhrazenou v okamžiku připsání na účet.",
            "Tento doklad byl vygenerován automatizovaným systémem.",
            "Při pozdní úhradě může být účtován úrok z prodlení ve výši 0.05% denně.",
            "Reklamace plnění je nutné uplatnit do 14 dnů od převzetí.",
            "Uchovávejte tento doklad pro účely případné reklamace a servisu.",
            "Všechny položky zůstávají majetkem dodavatele do úplného uhrazení.",
            "Smluvní vztah se řídí Všeobecnými obchodními podmínkami dodavatele.",
            "Tento doklad slouží zároveň jako dodací list, pokud není vystaven samostatně.",
            "Kupující stvrzuje převzetí zboží/služeb v uvedeném rozsahu a kvalitě.",
            "Data z tohoto dokladu jsou zpracovávána v souladu s nařízením GDPR.",
            "V případě dotazů kontaktujte naši zákaznickou podporu v pracovní dny 8-16h."
        ]
        
        random.shuffle(lorem_phrases)
        # Text nesmí vlézt do QR kódu, pokud jsme na stejné výšce
        text_max_w = width - qr_size - mm(5) 

        for phrase in lorem_phrases[:3]:
            full_phrase = f"• {phrase}"
            words = full_phrase.split(' ')
            line = ""
            
            for word in words:
                test_line = line + word + " "
                # Pokud jsme pod úrovní QR kódu, můžeme použít plnou šířku mm(100)
                current_limit = width if y > (start_y + qr_size + mm(5)) else text_max_w
                
                if text_width(test_line, inv._f10) < (current_limit - mm(2)):
                    line = test_line
                else:
                    inv._text(d, (x, y), text=line, font=inv._f10, fill=MUTED)
                    y += mm(3.5)
                    line = "  " + word + " " # Odsazení pro zalomený řádek
            
            inv._text(d, (x, y), text=line, font=inv._f10, fill=MUTED)
            y += mm(4.5)

        y += mm(2)
        
        # 4. "Eco-friendly" vata
        # Kolečko/lístek
        d.ellipse([x, y, x + mm(3), y + mm(3)], fill=LINE_MID)
        inv._text(d, (x + mm(4), y), text="Šetříme přírodu. Faktura v elektronické podobě.", font=inv._f10, fill=MUTED)

        return max(y + mm(5), start_y + qr_size + mm(10))

