from typing import final

from PIL import Image, ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.enumerates.SpanTag import SpanTag
from common.utils.consts import _A4_H_PX, _A4_W_PX
from common.utils.utilities import mm
from common.utils.utilities import safe, fmt_money


@final
class ColorfullInvoice(InvoiceTemplate):
    """Barevná faktura s gradientem a moderními prvky"""

    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        margin_l = mm(18)
        margin_r = mm(18)  
        margin_t = mm(15)
        margin_b = mm(15)

        # Světlé pozadí s nádechem barvy
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), (250, 251, 255))
        invoice.image = img
        d = ImageDraw.Draw(img)

        # Barevná paleta
        PRIMARY = (138, 43, 226)  # Fialová
        SECONDARY = (255, 105, 180)  # Růžová
        ACCENT = (30, 144, 255)  # Modrá
        DARK = (33, 37, 41)
        LIGHT_GRAY = (248, 249, 250)

        y = margin_t

        # --- BAREVNÁ HLAVIČKA S GRADIENTEM ---
        header_height = mm(30)
        
        # Simulace gradientu pomocí více obdélníků
        gradient_steps = 20
        for i in range(gradient_steps):
            step_height = header_height // gradient_steps
            # Interpolace mezi PRIMARY a SECONDARY
            ratio = i / gradient_steps
            r = int(PRIMARY[0] * (1 - ratio) + SECONDARY[0] * ratio)
            g = int(PRIMARY[1] * (1 - ratio) + SECONDARY[1] * ratio)
            b = int(PRIMARY[2] * (1 - ratio) + SECONDARY[2] * ratio)
            
            d.rectangle((0, i * step_height, _A4_W_PX, (i + 1) * step_height), fill=(r, g, b))

        # Text v hlavičce
        textRenderer._text(invoice,(margin_l, margin_t + mm(5)), safe(data.supplier.name), 
                    font=textRenderer._f20b, fill=(255, 255, 255))
        
        # Číslo faktury stylizované
        invoice_bg = (255, 255, 255, 180)  # Poloprůhledné pozadí
        textRenderer._text_right(invoice, _A4_W_PX - margin_r, margin_t, 
                        label="INVOICE #", text=f"{safe(data.invoice_number)}", font=textRenderer._f18b, fill=(255, 255, 255),
                        span_tag=SpanTag.INVOICE_NUMBER)

        y = header_height + mm(15)

        # --- INFORMAČNÍ KARTY ---
        card_height = mm(35)
        card_width = (_A4_W_PX - margin_l - margin_r - mm(15)) // 3

        # Karta 1 - Dodavatel
        card1_x = margin_l
        d.rectangle((card1_x, y, card1_x + card_width, y + card_height), 
                    fill=(255, 255, 255), outline=PRIMARY, width=2)
        d.rectangle((card1_x, y, card1_x + card_width, y + mm(6)), fill=PRIMARY)
        
        textRenderer._text(invoice,(card1_x + mm(3), y + mm(1)), "PRODÁVAJÍCÍ", font=textRenderer._f10b, fill=(255, 255, 255))
        textRenderer._text(invoice,(card1_x + mm(3), y + mm(8)), safe(data.supplier.name), font=textRenderer._f11b, fill=DARK)
        textRenderer._text(invoice,(card1_x + mm(3), y + mm(13)), safe(data.supplier.address)[:25], font=textRenderer._f9, fill=DARK)
        textRenderer._text(invoice,(card1_x + mm(3), y + mm(17)), label="IČ:", text=f"{safe(data.supplier.register_id)}", font=textRenderer._f9, fill=DARK,
                    span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        textRenderer._text(invoice,(card1_x + mm(3), y + mm(24)), label="DIČ:", text=f"{safe(data.supplier.tax_id)}", font=textRenderer._f9, fill=DARK,
                    span_tag=SpanTag.SUPPLIER_TAX_ID)

        # Karta 2 - Kupující  
        card2_x = margin_l + card_width + mm(7.5)
        d.rectangle((card2_x, y, card2_x + card_width, y + card_height), 
                    fill=(255, 255, 255), outline=ACCENT, width=2)
        d.rectangle((card2_x, y, card2_x + card_width, y + mm(6)), fill=ACCENT)
        
        textRenderer._text(invoice,(card2_x + mm(3), y + mm(1)), "KUPUJÍCÍ", font=textRenderer._f10b, fill=(255, 255, 255))
        textRenderer._text(invoice,(card2_x + mm(3), y + mm(8)), safe(data.customer.name), font=textRenderer._f11b, fill=DARK)
        textRenderer._text(invoice,(card2_x + mm(3), y + mm(13)), safe(data.customer.address)[:25], font=textRenderer._f9, fill=DARK)
        textRenderer._text(invoice,(card2_x + mm(3), y + mm(17)), label="IČ:", text=f"{safe(data.customer.register_id)}", font=textRenderer._f9, fill=DARK,
                    span_tag=SpanTag.CUSTOMER_REGISTER_ID)
        textRenderer._text(invoice,(card2_x + mm(3), y + mm(24)), label="DIČ:", text=f"{safe(data.customer.tax_id)}", font=textRenderer._f9, fill=DARK,
                    span_tag=SpanTag.CUSTOMER_TAX_ID)

        # Karta 3 - Platba
        card3_x = margin_l + 2 * card_width + mm(15)
        d.rectangle((card3_x, y, card3_x + card_width, y + card_height), 
                    fill=(255, 255, 255), outline=SECONDARY, width=2)
        d.rectangle((card3_x, y, card3_x + card_width, y + mm(6)), fill=SECONDARY)
        
        textRenderer._text(invoice,(card3_x + mm(3), y + mm(1)), "PLATBA", font=textRenderer._f10b, fill=(255, 255, 255))
        textRenderer._text(invoice,(card3_x + mm(3), y + mm(8)), label="Datum:", text=f"{safe(data.issue_date)}", font=textRenderer._f9, fill=DARK,
                    span_tag=SpanTag.ISSUE_DATE)
        textRenderer._text(invoice,(card3_x + mm(3), y + mm(12)), label="Splatnost:", text=f"{safe(data.due_date)}", font=textRenderer._f9, fill=DARK, span_tag=SpanTag.DUE_DATE)
        textRenderer._text(invoice,(card3_x + mm(3), y + mm(16)), label="VS: ", text=f"{safe(data.variable_symbol)}", font=textRenderer._f9, fill=DARK, span_tag=SpanTag.VARIABLE_SYMBOL)

        y += card_height + mm(20)

        # --- STYLIZOVANÁ TABULKA ---
        headers = ["Popis služby", "Množství", "Jednotka", "Cena/ks", "DPH%", "Celkem"]
        col_widths = [0.4, 0.12, 0.08, 0.15, 0.08, 0.17]
        table_width = _A4_W_PX - margin_l - margin_r
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin_l + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička s gradientem
        header_height = mm(10)
        for i in range(10):
            step_height = header_height // 10
            ratio = i / 10
            r = int(ACCENT[0] * (1 - ratio) + PRIMARY[0] * ratio)
            g = int(ACCENT[1] * (1 - ratio) + PRIMARY[1] * ratio) 
            b = int(ACCENT[2] * (1 - ratio) + PRIMARY[2] * ratio)
            
            d.rectangle((margin_l, y + i * step_height, _A4_W_PX - margin_r, 
                       y + (i + 1) * step_height), fill=(r, g, b))

        # Texty hlavičky
        for i, header in enumerate(headers):
            text_x = x_cols[i] + mm(3)
            if i in [1, 2, 4]:  # Střed pro množství, jednotku, DPH
                text_x = x_cols[i] + col_abs[i] // 2
                textRenderer._text_center(invoice, text_x, y + mm(2.5), header, textRenderer._f10b, (255, 255, 255), must_have_same_width=True)
            elif i in [3, 5]:  # Doprava pro ceny
                text_x = x_cols[i] + col_abs[i] - mm(3)
                textRenderer._text_right(invoice, text_x, y + mm(2.5), header, textRenderer._f10b, (255, 255, 255), must_have_same_width=True)
            else:  # Vlevo pro popis
                textRenderer._text(invoice,(text_x, y + mm(2.5)), header, font=textRenderer._f10b, fill=(255, 255, 255), must_have_same_width=True)

        y += header_height

        # Řádky s alternujícím pozadím
        row_height = mm(8)
        for i, item in enumerate(data.items):
            bg_color = (255, 255, 255) if i % 2 == 0 else (245, 247, 250)
            d.rectangle((margin_l, y, _A4_W_PX - margin_r, y + row_height), fill=bg_color)
            
            row_data = [
                safe(item.description),
                str(safe(item.quantity)),
                "ks",
                fmt_money(item.ppu),
                f"{safe(item.vat_percentage)}%",
                fmt_money(item.price_with_vat)
            ]
            
            for j, r_data in enumerate(row_data):
                text_y = y + mm(2)
                if j in [1, 2, 4]:  # Střed
                    textRenderer._text_center(invoice, x_cols[j] + col_abs[j] // 2, text_y, r_data, textRenderer._f9, DARK)
                elif j in [3, 5]:  # Doprava
                    textRenderer._text_right(invoice, x_cols[j] + col_abs[j] - mm(3), text_y, r_data, textRenderer._f9, DARK)
                else:  # Vlevo
                    textRenderer._text(invoice,(x_cols[j] + mm(3), text_y), r_data, font=textRenderer._f9, fill=DARK)
            
            y += row_height

        # --- CELKOVÁ ČÁSTKA S EFEKTEM ---
        y += mm(15)
        
        # Stínovaný box pro celkovou sumu
        shadow_offset = 3
        total_box_w = mm(70)
        total_box_h = mm(18)
        total_x = _A4_W_PX - margin_r - total_box_w
        
        # Stín
        d.rectangle((total_x + shadow_offset, y + shadow_offset, 
                    total_x + total_box_w + shadow_offset, y + total_box_h + shadow_offset), 
                    fill=(200, 200, 200))
        
        # Hlavní box
        d.rectangle((total_x, y, total_x + total_box_w, y + total_box_h), fill=PRIMARY)
        
        # Text
        total_text = f"CELKEM K ÚHRADĚ"
        textRenderer._text_center(invoice, total_x + total_box_w // 2, y + mm(4), 
                            total_text, textRenderer._f11b, (255, 255, 255))
        
        textRenderer._text_center(invoice, total_x + total_box_w // 2, y + mm(10), 
                            text=f"{fmt_money(data.calculated_total_price)}",
                            end=f"{data.currency.value}", font=textRenderer._f16b, fill=(255, 255, 255), span_tag=SpanTag.TOTAL)


        invoice.image = img
        return True
