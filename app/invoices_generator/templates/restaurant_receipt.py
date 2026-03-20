from typing import final
from PIL import Image, ImageDraw, ImageFont

from invoice_annotator.utils.GRelationship import GRelationship
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG
from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money



@final
class restaurant_receipt(DInvoice):
    """
    Vykreslí účtenku jako „papírový“ lístek
    """


    def generate_img(self, output_path: str) -> bool:
        # A4 plátno – účtenku vykreslíme jako úzký pás uprostřed
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        # Rozměr účtenky (lístku)
        ticket_w = mm(95)         # ~95 mm šířka pásky
        ticket_x = (self._A4_W_PX - ticket_w) // 2
        margin_t = mm(15)
        y = margin_t
        x0 = ticket_x
        x1 = ticket_x + ticket_w

        # Pomocné čáry
        def hr(ypos:int, weight:str="thin") -> None:
            color = LINE if weight == "thin" \
                else (LINE_MID if weight == "mid" else LINE_STRONG)
            width = 2 if weight in ("thin","mid") else 3
            d.line([(x0, ypos), (x1, ypos)], fill=color, width=width)

        # Horní okraj
        d.rectangle((x0, y, x1, y + mm(1)), fill=BG)
        y += mm(3)

        # --- HLAVIČKA (dynamicky ze supplier) ---
        supplier_name = safe(getattr(self.supplier, "name", ""))
        supplier_addr = safe(getattr(self.supplier, "address", ""))

        self._draw_center(d, (x0 + x1)//2, y, supplier_name or "—", self._f14b, INK)
        y += mm(6)
        # Druhý řádek (volitelný, např. „PIZZERIE…“ – použijeme supplier_name znovu, ať je to obecné)
        self._draw_center(d, (x0 + x1)//2, y, supplier_name, self._f10, MUTED)
        y += mm(5)
        if supplier_addr:
            self._draw_center(d, (x0 + x1)//2, y, supplier_addr, self._f10, MUTED)
            y += mm(3)
        else:
            y += mm(3)
        #IČ, DIČ
        x_now, _ = self._text(d, ((x0 + x1)//2 - mm(15), y), label="IČ: ", text=f"{self.supplier.register_id}", end=",", font=self._f10, fill=MUTED, span_tag=span_tags.SUPPLIER_REGISTER_ID)
        self._text(d, (x_now, y), label="DIČ: ", text=f"{self.supplier.tax_id}", font=self._f10, fill=MUTED, span_tag=span_tags.SUPPLIER_TAX_ID)
        y += mm(5)
        hr(y, "thin")
        y += mm(3)

        # --- META ÚDAJE ---
        kv_label_x = x0 + mm(3)
        kv_val_x = x1 - mm(3)

        def kv(label:str, value:str, bold:bool=False, tag:span_tags = span_tags.O, undersampling:bool = True) -> None:
            nonlocal y
            self._text(d,(kv_label_x, y), label, font=self._f11, fill=INK)
            self._draw_right(d, kv_val_x, y, safe(value), self._f11b if bold else self._f11, INK, span_tag=tag)
            y += mm(5)

        # mapování na invoice
        kv("Účtenka:", str(self.invoice_number), bold=True, tag=span_tags.INVOICE_NUMBER)
        kv("Objednávka:", str(self.variable_symbol), bold=True, tag=span_tags.VARIABLE_SYMBOL)  # není-li objednávka, použijeme VS
        kv("Datum:", self.issue_date, tag=span_tags.ISSUE_DATE)
        pay_str = self.payment_type
        kv("Způsob úhrady:", pay_str, tag=span_tags.PAYMENT_TYPE)
        y += mm(2)
        hr(y, "thin")
        y += mm(3)

        # --- TABULKA POLOŽEK ---
        col_name_w = int(ticket_w * 0.35)
        col_qty_w  = int(ticket_w * 0.19)
        col_price_w= int(ticket_w * 0.25)
        col_total_w= ticket_w - col_name_w - col_qty_w - col_price_w

        col_x = [
            x0,
            x0 + col_name_w,
            x0 + col_name_w + col_qty_w,
            x0 + col_name_w + col_qty_w + col_price_w,
            x1
        ]

        def th(txt:str, col:int, font:ImageFont.FreeTypeFont) -> None:
            cx = (col_x[col] + col_x[col+1])//2
            self._draw_center(d, cx, y, txt, font, INK)

        th("Název", 0, self._f11b); th("Počet", 1, self._f11b); th("Cena", 2, self._f11b); th("Celkem", 3, self._f11b)
        y += mm(6)
        hr(y, "mid")

        def row(name:str, qty:str, price:str, total:str) -> None:
            nonlocal y
            y += mm(2.5)
            self._text(d,(col_x[0] + mm(2), y), safe(name), font=self._f10, fill=INK)
            x_end, _ = self._draw_center(d, (col_x[1] + col_x[2])//2, y, safe(qty), self._f10, INK)
            self._text(d, (col_x[2], y), safe(price), self._f10, INK)
            self._draw_right(d, col_x[4] - mm(2), y, safe(total), self._f10, INK)
            y += mm(6)
            d.line([(x0, y), (x1, y)], fill=LINE, width=1)

        # řádky z self.items
        curr = self.currency.value if hasattr(self.currency, "value") else str(self.currency)
        for it in self.items:
            qty = getattr(it, "quantity", None)
            unit = getattr(it, "unit", "ks")
            qty_txt = f"{qty} {unit}" if qty is not None else ""
            if getattr(it, "ppu") is not None:
                ppu_val = it.ppu
            price_txt = f"{fmt_money(ppu_val)} {curr}" if ppu_val is not None else ""
            total_txt = f"{fmt_money(getattr(it, 'price_with_vat', 0))} {curr}"
            row(getattr(it, "description", ""), qty_txt, price_txt, total_txt)

        y += mm(3)

        # --- SOUHRN / TOTALY ---
        kv_label_x = x0 + mm(3)
        kv_val_x = x1 - mm(3)

        def total_line(label:str, value:str, end:str|None = None, big:bool=False, label_tag:span_tags=span_tags.O,tag:span_tags = span_tags.O) -> None:
            nonlocal y
            self._text(d,(kv_label_x, y), label, font=self._f11b if big else self._f11, fill=INK, span_tag=label_tag)
            x_n, _ = self._draw_right(d, kv_val_x, y, value, self._f12b if big else self._f11, INK, span_tag=tag)
            self._text(d, (x_n, y), end, self._f12b if big else self._f11, INK)
            y += mm(6 if big else 5)

        def total_line_summary(label0:str,label1:str, value0:str, value1:str,end0:str|None = None, end1:str|None = None, big0:bool=False, big1:bool=False,
                                label_tag0:span_tags=span_tags.O, label_tag1:span_tags=span_tags.O, tag0:span_tags = span_tags.O, tag1:span_tags = span_tags.O ) -> None:
            nonlocal y
            self._text(d,(kv_label_x, y), label0, font=self._f11b if big0 else self._f11, fill=INK, span_tag=label_tag0)
            x_n, base_id = self._draw_right(d, kv_val_x, y, value0, self._f12b if big0 else self._f11, INK, span_tag=tag0)
            self._text(d, (x_n, y), end0, self._f12b if big0 else self._f11, INK)
            y += mm(6 if big0 else 5)
            y += mm(2)

            _, percentage_id = self._text(d,(kv_label_x, y), label1, font=self._f11b if big1 else self._f11, fill=INK, span_tag=label_tag1)
            x_n, vat_id = self._draw_right(d, kv_val_x, y, value1, self._f12b if big1 else self._f11, INK, span_tag=tag1)
            self._text(d, (x_n, y), end1, self._f12b if big1 else self._f11, INK)
            
            y += mm(6 if big0 else 5)
            y += mm(2)
            
            self.append_relationship(GRelationship(None, base_id, percentage_id, relationship_types.BASE_OF))
            self.append_relationship(GRelationship(None, vat_id, percentage_id, relationship_types.VAT_OF))

            y += mm(2)

            return y



        # DPH po sazbách (dynamicky z self.vat)
        for v in self.vat:
            y = total_line_summary(label0=f"Základ ({safe(v.vat_percentage)}%)", value0=f"{fmt_money(v.vat_base)} ", end0=f"{curr}",label_tag0=span_tags.O, tag0=span_tags.VAT_BASE,
                        label1=f"DPH ({safe(v.vat_percentage)}%)", value1=f"{fmt_money(v.vat)} ", end1=f"{curr}", label_tag1=span_tags.VAT_PERCENTAGE, tag1=span_tags.VAT)
            hr(y, "thin")

            y += mm(2)


        # CELKEM
        hr(y, "mid"); y += mm(2.5)
        total_line(label="Celkem", value=f"{fmt_money(self.calculated_total_price)}", end=f"{curr}", big=True, tag=span_tags.TOTAL)

        y += mm(3)
        hr(y, "thin")
        y += mm(3)

        # --- ZÁKAZNÍK ---
        customer_name = safe(getattr(self.customer, "name", ""))
        if customer_name:
            self._text(d,(kv_label_x, y), "Zákazník:", font=self._f11, fill=INK)
            self._draw_right(d, kv_val_x, y, customer_name, self._f11b, INK)
            y += mm(6)

        # --- PATIČKA / POZNÁMKY ---
        y += mm(2)
        # „badge“ se způsobem úhrady
        badge_txt = f"Způsob úhrady: {pay_str}"
        w_badge = d.textlength(badge_txt, font=self._f10) + mm(6)
        bx0 = max(x0 + mm(2), (x0 + x1 - w_badge)//2)
        by0 = y
        by1 = by0 + mm(7)
        x_end, _ = self._draw_center(d, (x0 + x1)//2, by0 + mm(1.5), label="Způsob úhrady:", text=f"{pay_str}", font=self._f10, fill=INK, span_tag=span_tags.PAYMENT_TYPE)
        d.rectangle((bx0, by0, x_end, by1), outline=LINE, width=2, fill=None)
        y = by1 + mm(4)


        #img.show()
        # Uložení
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+mm(3)),word.tag.value, font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")
        return True
