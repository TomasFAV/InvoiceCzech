from typing import final

from PIL import Image, ImageDraw
from invoice_annotator.utils.GRelationship import GRelationship
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice

from invoices_generator.utility.invoice_consts import INK, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, BOX_BG
from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money


@final
class store_receipt(DInvoice):
    """
    Dynamická účtenka ve stylu 'DAŇOVÝ DOKLAD'
    """        

    def generate_img(self, output_path: str) -> bool:
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        # „termopáska“ uprostřed A4
        ticket_w = mm(95)  # ~95 mm šířky
        x0 = (self._A4_W_PX - ticket_w) // 2
        x1 = x0 + ticket_w
        y = mm(12)

        def hr(ypos:int, weight:str="thin")->None:
            color = LINE if weight=="thin" else (LINE_MID if weight=="mid" else LINE_STRONG)
            width = 2 if weight!="strong" else 3
            d.line([(x0, ypos), (x1, ypos)], fill=color, width=width)


        def kv_row(lbl:str, val:str, tag:span_tags = span_tags.O, undersampling:bool = True)->None:
            nonlocal y
            self._text(d,(x0+mm(3), y), lbl, font=self._f11, fill=INK)
            self._draw_right(d, x1-mm(3), y, safe(val), self._f11b, INK, span_tag=tag)
            y += mm(5)

        # ---------------- HLAVIČKA ----------------
        box_top = y
        d.rectangle((x0, y, x1, y+mm(10)), outline=LINE_STRONG, width=2, fill=SUBTLE_BG)
        self._draw_center(d,(x0+x1)//2,y+mm(2), "DAŇOVÝ  DOKLAD", self._f12b)
        y += mm(14)

        supplier_name = safe(getattr(self.supplier, "name", ""))
        supplier_addr = safe(getattr(self.supplier, "address", ""))
        supplier_dic  = safe(getattr(self.supplier, "tax_id", ""))
        supplier_ico  = safe(getattr(self.supplier, "register_id", ""))

        if supplier_name:
            self._draw_center(d,(x0+x1)//2,y, supplier_name, self._f11b); y += mm(5)
        if supplier_addr:
            self._draw_center(d,(x0+x1)//2,y, supplier_addr, self._f11); y += mm(5)
        if supplier_dic or supplier_ico:
            if supplier_dic:
                self._draw_center(d,(x0+x1)//2,y, label="DIČ: ", text=f"{supplier_dic}", font=self._f11, span_tag=span_tags.SUPPLIER_TAX_ID); y += mm(4.2)
            if supplier_ico:
                self._draw_center(d,(x0+x1)//2,y, label="IČO: ", text=f"{supplier_ico}", font=self._f11, span_tag=span_tags.SUPPLIER_REGISTER_ID); y += mm(5)

        hr(y, "thin"); y += mm(2)

        # ---------------- TABULKA HLAVIČKA ----------------
        # sloupce: počet | jedn.cena | sazba DP | cena
        pad = mm(3)
        col_w = [
            int(ticket_w*0.05),  # počet
            int(ticket_w*0.35),  # jedn.cena
            int(ticket_w*0.25),  # sazba
            ticket_w - int(ticket_w*0.25) - int(ticket_w*0.28) - int(ticket_w*0.20)  # cena
        ]
        col_x = [x0+pad, x0+pad+col_w[0], x0+pad+col_w[0]+col_w[1], x0+pad+col_w[0]+col_w[1]+col_w[2], x1-pad]

        def th(i:int, txt:str)->None:
            cx = (col_x[i] + col_x[i+1])//2
            self._draw_center(d, cx, y, txt, self._f11b, INK)

        th(0, "počet")
        th(1, "jedn.cena")
        th(2, "sazba DPH")
        th(3, "cena")
        y += mm(5.5)
        d.line([(x0+pad, y), (x1-pad, y)], fill=LINE_MID, width=2)
        y += mm(1.5)

        # ---------------- POLOŽKY ----------------
        # řádek položky v monospace
        def item_row(qty_txt:str, ppu_txt:str, vat_txt:str, price_txt:str)->None:
            nonlocal y
            # počet (vlevo), jednotková, sazba (střed), cena (vpravo)
            self._draw_right(d, col_x[1]-mm(1), y, qty_txt, self._f11, INK)
            self._draw_right(d, col_x[2]-mm(1), y, ppu_txt, self._f11, INK)
            self._draw_center(d, (col_x[2]+col_x[3])//2, y, vat_txt, self._f11, INK)
            self._draw_right(d, col_x[4], y, price_txt, self._f11, INK)
            y += mm(5.3)

        currency = self.currency.value if hasattr(self.currency, "value") else str(self.currency)

        for it in self.items:
            qty = it.quantity
            unit = getattr(it, "unit", "ks")
            ppu = it.ppu
            if ppu is None:
                try:
                    if qty not in (None, 0):
                        ppu = float(getattr(it, "price_with_vat", 0)) / float(qty)
                except Exception:
                    ppu = getattr(it, "price_with_vat", 0)

            # název (samostatný řádek)
            self._text(d,(x0+pad, y), safe(getattr(it, "description", "")), font=self._f11, fill=INK)
            y += mm(5)

            qty_txt = f"{safe(qty)} {unit}".strip()
            ppu_txt = f"{fmt_money(ppu)} {currency}" if ppu is not None else ""
            vat_txt = f"{safe(getattr(it, 'vat_percentage', ''))}%"
            price_txt = f"{fmt_money(getattr(it, 'price_with_vat', 0))} {currency}"
            item_row(qty_txt, ppu_txt, vat_txt, price_txt)

        hr(y, "thin"); y += mm(2)

        # ---------------- SOUHRN DPH ----------------
        # sazba   bez DPH   DPH   s DPH
        def sum_header()->None:
            nonlocal y
            self._draw_center(d, x0+pad + col_w[0]*0.35, y, "sazba", self._f11b, INK, must_have_same_width=True)
            self._draw_center(d, x0+pad + col_w[0] + col_w[1]*0.55, y, "bez DPH", self._f11b, INK, must_have_same_width=True)
            self._draw_center(d, x0+pad + col_w[0] + col_w[1] + col_w[2]*0.55, y, "DPH", self._f11b, INK, must_have_same_width=True)
            self._draw_center(d, x1-pad - col_w[3]*0.35, y, "s DPH", self._f11b, INK, must_have_same_width=True)
            y += mm(5)

        sum_header()
        for v in self.vat:
            # řádky souhrnu
            _, percentage_id = self._draw_center(d, x0+pad + col_w[0]*0.35, y, text=f"{safe(v.vat_percentage)}", end="%", font= self._f11,fill=INK, span_tag=span_tags.VAT_PERCENTAGE)
            _, base_id = self._draw_right(d, x0+pad + col_w[0] + col_w[1] - mm(2), y, text=f"{fmt_money(v.vat_base)}", end=f"{currency}", font= self._f11, fill=INK, span_tag=span_tags.VAT_BASE)
            _, vat_id = self._draw_right(d, x0+pad + col_w[0] + col_w[1] + col_w[2] - mm(2), y, f"{fmt_money(v.vat)}", end=f"{currency}", font=self._f11, fill=INK, span_tag=span_tags.VAT)
            self._draw_right(d, x1-pad, y, f"{fmt_money(float(v.vat_base) + float(v.vat))} {currency}", self._f11, INK)
            y += mm(5)

            self.append_relationship(GRelationship(None, base_id, percentage_id, relationship_types.BASE_OF))
            self.append_relationship(GRelationship(None, vat_id, percentage_id, relationship_types.VAT_OF))

        # CELKEM
        y += mm(1)
        d.rectangle((x0, y, x1, y+mm(9)), outline=LINE_STRONG, width=2, fill=BOX_BG)
        self._draw_center(d, (x0+x1)//2, y+mm(2), "CELKEM", self._f11b, INK)
        self._draw_right(d, x1-mm(4), y+mm(2), text=f"{fmt_money(self.calculated_total_price)}", end=f"{currency}", font=self._f11b, fill=INK, span_tag=span_tags.TOTAL)
        y += mm(12)

        # ---------------- PATIČKA / META ----------------
        hr(y, "thin"); y += mm(3)

        
        kv_row("Účtenka:", str(self.invoice_number), tag=span_tags.INVOICE_NUMBER)
        kv_row("Vystaveno:", self.issue_date, tag=span_tags.ISSUE_DATE)

        # Volitelné: číslo pokladny / pokladník – pokud je v description/customer apod.
        cashier = safe(getattr(self.customer, "name", ""))  # když eviduješ pokladníka jako "customer.name"
        if cashier:
            kv_row("Pokladník:", cashier)


        y += mm(2)
        self._draw_center(d,(x0+x1)//2,y, "----  DĚKUJEME  ----", self._f11b)
        y += mm(6)

        #img.show()
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+mm(3)),word.tag.value, font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")
        return True
