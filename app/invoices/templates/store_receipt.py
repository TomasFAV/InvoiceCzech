import json
from typing import Any, Dict, final
from PIL import Image, ImageDraw, ImageFont
from app.invoices.core.invoice import invoice
from app.invoices.utility.json_encoder import json_encoder

@final
class store_receipt(invoice):
    """
    Dynamická účtenka ve stylu 'DAŇOVÝ DOKLAD'
    """        
    
    def to_json(self)->Any:
        data:Dict[str, Any] = dict(issue_date=self.issue_date, due_date=self.issue_date, taxable_supply_date=self.issue_date,
                    payment=self.payment.value, bank=self.bank_account, bank_account_number=self.bank_account_number, IBAN = self.IBAN, 
                    variable_symbol="", const_symbol="", 
                    supplier = self.supplier, customer = self.customer,
                    items = self.items, vat_items = self.vat, rounding = self.rounding,
                    total_price = self.calculated_total_price, total_vat = self.calculated_total_vat, currency = self.currency,
                    invoice_number = self.invoice_number)

        #zrušení vazeb na instance bank, zákazníků, dodavatelů
        j_data:Dict[str, Any] = json.loads(json.dumps(data, cls = json_encoder, ensure_ascii=False))

        #Mazání informací, které nejsou z faktury dostupné
        j_data["total_vat"] = None
        j_data["customer"]["street"] = ""
        j_data["customer"]["zip"] = ""
        j_data["customer"]["city"] = ""
        j_data["customer"]["country"] = ""
        j_data["customer"]["register_id"] = ""
        j_data["customer"]["type"] = ""
        j_data["customer"]["tax_id"] = ""
        j_data["customer"]["street"] = ""
        j_data["customer"]["name"] = self.customer.name
        j_data["supplier"]["phone"] = ""
        j_data["supplier"]["type"] = ""
        j_data["rounding"] = None

        j_data["bank"]["name"] = ""
        j_data["bank_account_number"] = ""
        j_data["bank"]["code"] = ""
        j_data["IBAN"] = ""
        j_data["bank"]["BIC"] = ""

        for item in j_data["items"]:
            item["vat"] = None
            item["price_without_vat"] = None

        return j_data

    def generate_img(self, output_path: str) -> bool:
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        # „termopáska“ uprostřed A4
        ticket_w = self.mm(80)  # ~80 mm šířky
        x0 = (self._A4_W_PX - ticket_w) // 2
        x1 = x0 + ticket_w
        y = self.mm(12)

        def hr(ypos:int, weight:str="thin")->None:
            color = self._LINE if weight=="thin" else (self._LINE_MID if weight=="mid" else self._LINE_STRONG)
            width = 2 if weight!="strong" else 3
            d.line([(x0, ypos), (x1, ypos)], fill=color, width=width)

        def text_center(ypos:int, txt:str, font:ImageFont.FreeTypeFont)->None:
            self._draw_center(d, (x0+x1)//2, ypos, txt, font, self._INK)

        def kv_row(lbl:str, val:str)->None:
            nonlocal y
            d.text((x0+self.mm(3), y), lbl, font=self._f11, fill=self._INK)
            self._draw_right(d, x1-self.mm(3), y, self._safe(val), self._f11b, self._INK)
            y += self.mm(5)

        # ---------------- HLAVIČKA ----------------
        box_top = y
        d.rectangle((x0, y, x1, y+self.mm(10)), outline=self._LINE_STRONG, width=2, fill=self._SUBTLE_BG)
        text_center(y+self.mm(2), "DAŇOVÝ  DOKLAD", self._f12b)
        y += self.mm(14)

        supplier_name = self._safe(getattr(self.supplier, "name", ""))
        supplier_addr = self._safe(getattr(self.supplier, "address", ""))
        supplier_dic  = self._safe(getattr(self.supplier, "tax_id", ""))
        supplier_ico  = self._safe(getattr(self.supplier, "register_id", ""))

        if supplier_name:
            text_center(y, supplier_name, self._f11b); y += self.mm(5)
        if supplier_addr:
            text_center(y, supplier_addr, self._f11); y += self.mm(5)
        if supplier_dic or supplier_ico:
            if supplier_dic:
                text_center(y, f"DIČ: {supplier_dic}", self._f11); y += self.mm(4.2)
            if supplier_ico:
                text_center(y, f"IČO: {supplier_ico}", self._f11); y += self.mm(5)

        hr(y, "thin"); y += self.mm(2)

        # ---------------- TABULKA HLAVIČKA ----------------
        # sloupce: počet | jedn.cena | sazba DP | cena
        pad = self.mm(3)
        col_w = [
            int(ticket_w*0.25),  # počet
            int(ticket_w*0.28),  # jedn.cena
            int(ticket_w*0.20),  # sazba
            ticket_w - int(ticket_w*0.25) - int(ticket_w*0.28) - int(ticket_w*0.20)  # cena
        ]
        col_x = [x0+pad, x0+pad+col_w[0], x0+pad+col_w[0]+col_w[1], x0+pad+col_w[0]+col_w[1]+col_w[2], x1-pad]

        def th(i:int, txt:str)->None:
            cx = (col_x[i] + col_x[i+1])//2
            self._draw_center(d, cx, y, txt, self._f11b, self._INK)

        th(0, "počet")
        th(1, "jedn.cena")
        th(2, "sazba DP")
        th(3, "cena")
        y += self.mm(5.5)
        d.line([(x0+pad, y), (x1-pad, y)], fill=self._LINE_MID, width=2)
        y += self.mm(1.5)

        # ---------------- POLOŽKY ----------------
        # řádek položky v monospace
        def item_row(qty_txt:str, ppu_txt:str, vat_txt:str, price_txt:str)->None:
            nonlocal y
            # počet (vlevo), jednotková, sazba (střed), cena (vpravo)
            self._draw_right(d, col_x[1]-self.mm(1), y, qty_txt, self._f11, self._INK)
            self._draw_right(d, col_x[2]-self.mm(1), y, ppu_txt, self._f11, self._INK)
            self._draw_center(d, (col_x[2]+col_x[3])//2, y, vat_txt, self._f11, self._INK)
            self._draw_right(d, col_x[4], y, price_txt, self._f11, self._INK)
            y += self.mm(5.3)

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
            d.text((x0+pad, y), self._safe(getattr(it, "description", "")), font=self._f11, fill=self._INK)
            y += self.mm(5)

            qty_txt = f"{self._safe(qty)} {unit}".strip()
            ppu_txt = f"{self._fmt_money(ppu)} {currency}" if ppu is not None else ""
            vat_txt = f"{self._safe(getattr(it, 'vat_percentage', ''))} %"
            price_txt = f"{self._fmt_money(getattr(it, 'price_with_vat', 0))} {currency}"
            item_row(qty_txt, ppu_txt, vat_txt, price_txt)

        hr(y, "thin"); y += self.mm(2)

        # ---------------- SOUHRN DPH ----------------
        # sazba   bez DPH   DPH   s DPH
        def sum_header()->None:
            nonlocal y
            self._draw_center(d, x0+pad + col_w[0]*0.35, y, "sazba", self._f11b, self._INK)
            self._draw_center(d, x0+pad + col_w[0] + col_w[1]*0.55, y, "bez DPH", self._f11b, self._INK)
            self._draw_center(d, x0+pad + col_w[0] + col_w[1] + col_w[2]*0.55, y, "DPH", self._f11b, self._INK)
            self._draw_center(d, x1-pad - col_w[3]*0.35, y, "s DPH", self._f11b, self._INK)
            y += self.mm(5)

        sum_header()
        for v in self.vat:
            # řádky souhrnu
            self._draw_center(d, x0+pad + col_w[0]*0.35, y, f"{self._safe(v.vat_percentage)} %", self._f11, self._INK)
            self._draw_right(d, x0+pad + col_w[0] + col_w[1] - self.mm(2), y, f"{self._fmt_money(v.vat_base)} {currency}", self._f11, self._INK)
            self._draw_right(d, x0+pad + col_w[0] + col_w[1] + col_w[2] - self.mm(2), y, f"{self._fmt_money(v.vat)} {currency}", self._f11, self._INK)
            self._draw_right(d, x1-pad, y, f"{self._fmt_money(v.vat_base + v.vat)} {currency}", self._f11, self._INK)
            y += self.mm(5)

        # CELKEM
        y += self.mm(1)
        d.rectangle((x0, y, x1, y+self.mm(9)), outline=self._LINE_STRONG, width=2, fill=self._BOX_BG)
        self._draw_center(d, (x0+x1)//2, y+self.mm(2), "C E L K E M", self._f11b, self._INK)
        self._draw_right(d, x1-self.mm(4), y+self.mm(2), f"{self._fmt_money(self.calculated_total_price)} {currency}", self._f11b, self._INK)
        y += self.mm(12)

        # ---------------- PATIČKA / META ----------------
        hr(y, "thin"); y += self.mm(3)

        if self._safe(self.invoice_number):
            kv_row("Účtenka:", str(self.invoice_number))
        if self._safe(self.issue_date):
            kv_row("Vystaveno:", self.issue_date)

        # Volitelné: číslo pokladny / pokladník – pokud je v description/customer apod.
        cashier = self._safe(getattr(self.customer, "name", ""))  # když eviduješ pokladníka jako "customer.name"
        if cashier:
            kv_row("Pokladník:", cashier)


        y += self.mm(2)
        text_center(y, "----  DĚKUJEME  ----", self._f11b)
        y += self.mm(6)

        #img.show()
        self.post_process(img).save(output_path, format="PNG", quality=100, subsampling=0)
        return True
