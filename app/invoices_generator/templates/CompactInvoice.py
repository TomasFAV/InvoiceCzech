from typing import final
from PIL import Image, ImageDraw

from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.enumerates.SpanTag import SpanTag
from common.utils.consts import _A4_H_PX, _A4_W_PX

from common.utils.utilities import mm
from common.utils.utilities import safe, fmt_money


@final
class CompactInvoice(InvoiceTemplate):
    """Kompaktní faktura s hustším layoutem a menšími fonty"""
    
    
    def render(textRenderer:TextRenderer, data: InvoiceData, invoice:Invoice) -> bool:
        # Menší okraje pro kompaktní design
        margin = mm(10)
        
        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), (255, 255, 255))
        invoice.image = img
        d = ImageDraw.Draw(img)

        DARK_BLUE = (25, 42, 86)
        LIGHT_BLUE = (74, 144, 226)
        GRAY = (95, 99, 104)

        y = margin

        # --- KOMPAKTNÍ HLAVIČKA ---
        # Barevný pruh nahoře
        d.rectangle((0, 0, _A4_W_PX, mm(6)), fill=DARK_BLUE)
        
        y += mm(8)
        
        # Informace v jednom řádku
        textRenderer._text(invoice,(margin, y), label=f"{safe(data.supplier.name)} | FAKTURA", text=f"{safe(data.invoice_number)}", 
                    font=textRenderer._f14b, fill=DARK_BLUE, span_tag=SpanTag.INVOICE_NUMBER)
        
        # Datum vpravo
        textRenderer._text_right(invoice, _A4_W_PX - margin, y, label="Datum: ", text=f"{safe(data.issue_date)}", 
                        font=textRenderer._f12, fill=GRAY, span_tag=SpanTag.ISSUE_DATE)
        
        y += mm(12)

        # --- ÚDAJE VE DVOU SLOUPCÍCH ---
        col_width = (_A4_W_PX - 2 * margin - mm(10)) // 2
        
        # Levý sloupec - dodavatel
        textRenderer._text(invoice,(margin, y), "DODAVATEL", font=textRenderer._f10b, fill=LIGHT_BLUE)
        y += mm(4)
        textRenderer._text(invoice,(margin, y), safe(data.supplier.name), font=textRenderer._f11b, fill=DARK_BLUE)
        y += mm(4)
        textRenderer._text(invoice,(margin, y), safe(data.supplier.address), font=textRenderer._f9, fill=GRAY)
        y += mm(3)
        x_end, _ = textRenderer._text(invoice,(margin, y), label="IČ: ", text=f"{safe(data.supplier.register_id)}", 
                            font=textRenderer._f9, fill=GRAY, span_tag=SpanTag.SUPPLIER_REGISTER_ID)
        textRenderer._text(invoice,(x_end, y), label="| DIČ: ", text=f"{safe(data.supplier.tax_id)}", 
                            font=textRenderer._f9, fill=GRAY, span_tag=SpanTag.SUPPLIER_TAX_ID)

        # Pravý sloupec - odběratel
        customer_x = margin + col_width + mm(10)
        customer_y = y - mm(11)  # Začínáme na stejné výši
        
        textRenderer._text(invoice,(customer_x, customer_y), "ODBĚRATEL", font=textRenderer._f10b, fill=LIGHT_BLUE)
        customer_y += mm(4)
        textRenderer._text(invoice,(customer_x, customer_y), safe(data.customer.name), font=textRenderer._f11b, fill=DARK_BLUE)
        customer_y += mm(4)
        textRenderer._text(invoice,(customer_x, customer_y), safe(data.customer.address), font=textRenderer._f9, fill=GRAY)
        customer_y += mm(3)
        textRenderer._text(invoice,(customer_x, customer_y), label="IČ: ", text=f"{safe(data.customer.register_id)}", font=textRenderer._f9, fill=GRAY, span_tag=SpanTag.CUSTOMER_REGISTER_ID)
        customer_y += mm(3)
        textRenderer._text(invoice,(customer_x, customer_y), label="DIČ: ", text=f"{safe(data.customer.tax_id)}", font=textRenderer._f9, fill=GRAY, span_tag=SpanTag.CUSTOMER_TAX_ID)
        
        y += mm(15)

        # --- PLATEBNÍ INFO V ŘÁDKU ---
        x_end, _ = textRenderer._text(invoice,(margin, y), label="Splatnost: ", text=f"{safe(data.due_date)}",font=textRenderer._f10, fill=GRAY, span_tag=SpanTag.DUE_DATE)
        x_end, _ = textRenderer._text(invoice,(x_end, y), label="| Platba: ", text=f"{safe(data.payment_type)}",font=textRenderer._f10, fill=GRAY, span_tag=SpanTag.PAYMENT_TYPE)
        x_end, _ = textRenderer._text(invoice,(x_end, y), label="| VS: ", text=f"{safe(data.variable_symbol)}",font=textRenderer._f10, fill=GRAY, span_tag=SpanTag.VARIABLE_SYMBOL)

        y += mm(10)
        
        # Tenká linka
        d.line([(margin, y), (_A4_W_PX - margin, y)], fill=LIGHT_BLUE, width=1)
        y += mm(8)

        # --- KOMPAKTNÍ TABULKA ---
        headers = ["Položka", "Ks", "Cena", "Celkem"]
        col_widths = [0.6, 0.1, 0.15, 0.15]
        table_width = _A4_W_PX - 2 * margin
        col_abs = [int(w * table_width) for w in col_widths]
        x_cols = [margin + sum(col_abs[:i]) for i in range(len(col_abs))]

        # Hlavička tabulky
        header_height = mm(8)
        for i, header in enumerate(headers):
            if i == 0:  # Položka vlevo
                textRenderer._text(invoice,(x_cols[i] + mm(2), y), header, font=textRenderer._f10b, fill=DARK_BLUE, must_have_same_width=True)
            elif i == 1:  # Ks na střed
                textRenderer._text_center(invoice, x_cols[i] + col_abs[i] // 2, y, header, textRenderer._f10b, DARK_BLUE, must_have_same_width=True)
            else:  # Ceny doprava
                textRenderer._text_right(invoice, x_cols[i] + col_abs[i] - mm(2), y, header, textRenderer._f10b, DARK_BLUE, must_have_same_width=True)

        y += header_height
        d.line([(margin, y), (_A4_W_PX - margin, y)], fill=DARK_BLUE, width=2)

        # Řádky položek
        row_height = mm(6)
        for item in data.items:
            y += row_height
            
            # Obsah řádku
            textRenderer._text(invoice,(x_cols[0] + mm(2), y - mm(4)), safe(item.description)[:40], font=textRenderer._f9, fill=DARK_BLUE)
            
            textRenderer._text_center(invoice, x_cols[1] + col_abs[1] // 2, y - mm(4), 
                            str(safe(item.quantity)), textRenderer._f9, DARK_BLUE)
            
            textRenderer._text_right(invoice, x_cols[2] + col_abs[2] - mm(2), y - mm(4), 
                            fmt_money(item.ppu), textRenderer._f9, DARK_BLUE)
            
            textRenderer._text_right(invoice, x_cols[3] + col_abs[3] - mm(2), y - mm(4), 
                            fmt_money(item.price_with_vat), textRenderer._f9, DARK_BLUE)
            
            # Tenká linka
            d.line([(margin, y), (_A4_W_PX - margin, y)], fill=(220, 220, 220), width=1)

        # Celkova suma
        y += mm(5)
        
        textRenderer._text(invoice, (margin, y), 
                        label="CELKEM: ", text=f"{data.calculated_total_price}",end=f"{data.currency.value}", font=textRenderer._f11b, fill=GRAY,
                        span_tag=SpanTag.TOTAL)

        y += mm(20)

        # --- PLATEBNÍ ÚDAJE V PATIČCE ---
        textRenderer._text(invoice,(margin, y), label="Číslo účtu: ", text=f"{safe(data.bank_account_number)}", font=textRenderer._f9, fill=GRAY,
                    span_tag=SpanTag.BANK_ACCOUNT_NUMBER)

        # Uložení
        invoice.image = img
        return True
