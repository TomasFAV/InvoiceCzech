from PIL.ImageDraw import ImageDraw
from abc import ABC, abstractmethod
import random

from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.utility.utils import mm, load_font, get_iou, text_width, get_tesseract_words, get_random_style, draw_styled_rect
from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import safe, fmt_money, get_item_value

from PIL.ImageFont import truetype, FreeTypeFont

class vat_c(invoice_component):



    @staticmethod
    def draw(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        width: int = kwargs.get("width", None)
        height: int = kwargs.get("height", None)
        
        if not height or not width:
            return vat_c.draw_normal(inv, d, x,y, width=width, height=height)
        else:
            return vat_c.draw_scaled(inv, d, x,y, width=width, height=height)
    
    def draw_scaled(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        # Šířka jednoho badge
        width = kwargs.get("width", mm(75))
        height = kwargs.get("height", mm(75))
        
        row_height = row_height = min(float(height)/len(inv.vat), 75) #75px max

        font_size_f8b = row_height * 0.2
        font_size_f9 = row_height * 0.25
        font_size_f10b = row_height * 0.3

        scaled_f8b = truetype(inv._f8b.path, font_size_f8b)
        scaled_f9 = truetype(inv._f9.path, font_size_f9)
        scaled_f10b = truetype(inv._f10b.path, font_size_f10b)

        for v in inv.vat:
            # 1. Vykreslení zaobleného obdélníku pro každou sazbu
            # Použijeme velmi světlé pozadí a tenký outline
            d.rounded_rectangle(
                [x, y, x + width, y + row_height], 
                radius=mm(1), fill=(253, 253, 253), outline=LINE_MID
            )
            
            # Levý "proužek" pro barevný akcent
            d.rectangle([x, y + row_height*0.1, x + mm(1), y + row_height - row_height*0.1], fill=INK)

            # 2. Vykreslení hodnot
            curr_x = x + width*0.05
            
            # SAZBA (jako malý tučný popisek)
            inv._text(d, (curr_x, y + row_height*0.1), label="DPH", text=f"{v.vat_percentage}", end="%", 
                     font=scaled_f8b, fill=MUTED, span_tag=span_tags.VAT_PERCENTAGE)
            
            # ZÁKLAD (Zarovnaný vlevo pod sazbu nebo vedle)
            inv._text(d, (curr_x, y + row_height*0.6), text="Základ:", font=scaled_f8b, fill=MUTED)
            inv._text(d, (curr_x + width*0.1, y + row_height*0.6), text=fmt_money(v.vat_base), 
                     font=scaled_f9, fill=INK, span_tag=span_tags.VAT_BASE)
            
            # DAŇ (Výrazně vpravo)
            # Štítek "Daň"
            inv._draw_right(d, x + width - width*0.1, y + row_height*0.1, text="VÝŠE DANĚ", 
                           font=scaled_f8b, fill=MUTED)
            # Samotná částka daně
            inv._draw_right(d, x + width - width*0.1, y + row_height*0.6, text=fmt_money(v.vat), 
                           font=scaled_f10b, fill=INK, span_tag=span_tags.VAT)

            y += row_height + row_height*0.05 # Mezera mezi badges
            
        return y + mm(2)

    def draw_normal(inv: DInvoice, d: ImageDraw, x: int, y: int, **kwargs):
        # Šířka jednoho badge
        badge_w = kwargs.get("width", None)
        if badge_w is None:
            badge_w = mm(75)
        badge_h = mm(10)
        
        for v in inv.vat:
            # 1. Vykreslení zaobleného obdélníku pro každou sazbu
            # Použijeme velmi světlé pozadí a tenký outline
            d.rounded_rectangle(
                [x, y, x + badge_w, y + badge_h], 
                radius=mm(1), fill=(253, 253, 253), outline=LINE_MID
            )
            
            # Levý "proužek" pro barevný akcent
            d.rectangle([x, y + mm(2), x + mm(1), y + badge_h - mm(2)], fill=INK)

            # 2. Vykreslení hodnot
            curr_x = x + mm(4)
            
            # SAZBA (jako malý tučný popisek)
            inv._text(d, (curr_x, y + mm(1.5)), label="DPH", text=f"{v.vat_percentage}", end="%", 
                     font=inv._f8b, fill=MUTED, span_tag=span_tags.VAT_PERCENTAGE)
            
            # ZÁKLAD (Zarovnaný vlevo pod sazbu nebo vedle)
            inv._text(d, (curr_x, y + mm(4.5)), text="Základ:", font=inv._f8, fill=MUTED)
            inv._text(d, (curr_x + mm(10), y + mm(4.5)), text=fmt_money(v.vat_base), 
                     font=inv._f9, fill=INK, span_tag=span_tags.VAT_BASE)
            
            # DAŇ (Výrazně vpravo)
            # Štítek "Daň"
            inv._draw_right(d, x + badge_w - mm(3), y + mm(1.5), text="VÝŠE DANĚ", 
                           font=inv._f8b, fill=MUTED)
            # Samotná částka daně
            inv._draw_right(d, x + badge_w - mm(3), y + mm(4.5), text=fmt_money(v.vat), 
                           font=inv._f10b, fill=INK, span_tag=span_tags.VAT)

            y += badge_h + mm(2) # Mezera mezi badges
            
        return y + mm(2)
