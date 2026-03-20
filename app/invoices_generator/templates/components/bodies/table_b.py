from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money, get_item_value

from PIL.ImageFont import truetype

class table_b(invoice_component):

    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        width: int = kwargs.get("width", None)
        height: int = kwargs.get("height", None)

        # Konfigurace - odebral jsem DPH, aby to bylo vzdušnější (nebo ho tam nech)
        config = [
            ("Položka", "description", 0.2),
            ("ks", "quantity", 0.1),
            ("DPH %", "vat_percentage", 0.2),
            ("Jedn. cena", "ppu", 0.2),
            ("Celkem", "price_with_vat", 0.3)
        ]

        if not width:
            width = mm(170)

        if not height:
            height = mm(80)

        random.shuffle(config)

        #plus hlavička
        row_height = min(float(height) / (len(inv.items) + 1), 50) #max 50px
        
        font_size_f8 = row_height * 0.3
        font_size_f9 = row_height * 0.35
        font_size_f9b = row_height * 0.37
        font_size_f10 = row_height * 0.45
        font_size_f10b = row_height * 0.47
        font_size_f13b = row_height * 0.55

        scaled_f8 = truetype(inv._f8.path, font_size_f8)
        scaled_f9 = truetype(inv._f9.path, font_size_f9)
        scaled_f9b = truetype(inv._f9b.path, font_size_f9b)
        scaled_f10 = truetype(inv._f10.path, font_size_f10)
        scaled_f10b = truetype(inv._f10b.path, font_size_f10b)
        scaled_f13b = truetype(inv._f13b.path, font_size_f13b)

        table_w = width
        
        col_widths = [int(col[2] * table_w) for col in config]
        
    

        # Výpočet pozic sloupců
        x_cols = [x]
        for w in col_widths[:-1]:
            x_cols.append(x_cols[-1] + w)

        # 1. HLAVIČKA (Moderní bez linek, jen podkladový pás)
        d.rectangle([x, y, x + table_w, y + row_height * 0.7], fill=SUBTLE_BG)
        for i, col in enumerate(config):
            # První sloupec vlevo, ostatní doprava
            if i == 0:
                inv._text(d, (x_cols[i] + width*0.05, y + row_height*0.05), col[0], font=scaled_f10b, fill=MUTED)
            else:
                inv._draw_right(d, x_cols[i] + col_widths[i] - width*0.05, y + row_height*0.05, col[0], font=scaled_f10b, fill=MUTED)
        
        y += row_height * 0.7

        # 2. POLOŽKY
        for idx, it in enumerate(inv.items):
            start_y = y
            
            # Vykreslení dat
            for i, col in enumerate(config):
                val = get_item_value(it, col[1])
                
                if i == 0:
                    # Popis položky tučněji
                    inv._text(d, (x_cols[i] + width*0.05, y), fmt_money(val), font=scaled_f9b, fill=INK)
                else:
                    # Ostatní hodnoty normálně
                    inv._draw_right(d, x_cols[i] + col_widths[i] - width*0.05, y, fmt_money(val), font=scaled_f9, fill=INK)
            
            y += row_height*0.4
            
            # Sub-text (vytvoříme vatu: kód produktu nebo popis dph)
            inv._text(d, (x_cols[0] + width*0.05, y), f"Kód: {random.randint(1000,9999)}", font=scaled_f8, fill=MUTED)
            
            y += row_height*0.4
            # Jemná linka mezi položkami
            d.line([(x + width*0.05, y), (x + table_w - width*0.05, y)], fill=LINE, width=1)
            y += row_height*0.2

        # 3. ZÁVĚREČNÉ SHRNUTÍ (Tečkovaná čára a velký Total)
        y += row_height*0.2
        d.line([(x, y), (x + table_w, y)], fill=LINE_STRONG, width=1)
        y += row_height*0.2
        
        total_label = "CELKEM K ÚHRADĚ"
        total_val = f"{fmt_money(inv.total_price)}"
        
        inv._draw_right(d, x + table_w - width*0.2, y, total_label, font=scaled_f10b, fill=INK)
        inv._draw_right(d, x + table_w - width*0.05, y - row_height*0.05, text=total_val, end="Kč", font=scaled_f13b, fill=INK, span_tag=span_tags.TOTAL)

        return y + mm(5)