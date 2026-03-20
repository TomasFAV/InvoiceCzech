from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money



class lorem_b(invoice_component):

    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        # Respektujeme zadanou šířku nebo default mm(100)
        max_w = kwargs.get("width", mm(85))
        start_y = y

        # 1. SEKCE: PODPIS A RAZÍTKO
        # Box pro podpis (trochu užší, aby zbylo místo na razítko v mm(100))
        box_w, box_h = mm(45), mm(20)
        d.rectangle([x, y, x + box_w, y + box_h], outline=LINE_MID, width=1)
        inv._text(d, (x + mm(2), y + box_h + mm(1)), text="Razítko a podpis", font=inv._f8, fill=MUTED)

        # Simulace ručního podpisu
        sig_color = (20, 40, 150) 
        for _ in range(15):
            x1 = x + mm(5) + random.randint(0, int(box_w - mm(10)))
            y1 = y + mm(5) + random.randint(0, int(box_h - mm(10)))
            x2 = x1 + random.randint(-mm(5), mm(10))
            y2 = y1 + random.randint(-mm(3), mm(3))
            d.line([x1, y1, x2, y2], fill=sig_color, width=random.randint(1, 2))

        # Simulace razítka - posunuto tak, aby nepřelezlo max_w
        stamp_r = mm(10)
        stamp_x = x + max_w - (stamp_r * 2) - mm(2) # Zarovnáno k pravému okraji mm(100)
        
        d.ellipse([stamp_x, y, stamp_x + stamp_r*2, y + stamp_r*2], outline=(180, 40, 40), width=2)
        inv._text(d, (stamp_x + mm(4), y + mm(8)), text="SCHVÁLENO", font=inv._f8b, fill=(180, 40, 40))

        y += box_h + mm(10)

        # 2. SEKCE: DROBNÝ TEXT (s hlídáním šířky)
        fine_print = [
            "Tento doklad byl vystaven v souladu s obchodními podmínkami platnými od 1.1.2026.",
            "Dodavatel je zapsán v obchodním rejstříku vedeném u Městského soudu v Praze, oddíl C, vložka 123456.",
            "Nejsme plátci DPH (pokud není uvedeno jinak). Režim přenesené daňové povinnosti dle § 92a zákona o DPH."
        ]
        
        for phrase in fine_print:
            # Kontrola šířky textu - pokud je delší než max_w, rozdělíme ho
            words = phrase.split(' ')
            line = ""
            for word in words:
                test_line = line + word + " "
                # text_width je pomocná funkce, kterou už v projektu máš
                if text_width(test_line, inv._f8) < (max_w - mm(5)):
                    line = test_line
                else:
                    inv._text(d, (x, y), text=line, font=inv._f8, fill=MUTED)
                    y += mm(3)
                    line = word + " "
            
            # Vykreslení zbytku řádku
            inv._text(d, (x, y), text=line, font=inv._f8, fill=MUTED)
            y += mm(4) # Mezera mezi odstavci

        return y + mm(5)

