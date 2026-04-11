import random
import re
from PIL.ImageFont import FreeTypeFont

from common.utils.utilities import fit_line_bounding_box_font, text_height, text_width
from common.data.invoice_consts import invoice_term_variants_expanded


class InvoiceTextParaphraser:


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