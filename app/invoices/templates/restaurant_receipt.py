import json
from typing import Any, Dict, final
from PIL import Image, ImageDraw, ImageFont
from app.invoices.core.invoice import invoice
from app.invoices.utility.json_encoder import json_encoder

@final
class restaurant_receipt(invoice):
    """
    Vykreslí účtenku jako „papírový“ lístek
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
            item["vat_percentage"] = None
            item["price_without_vat"] = None

        return j_data

    def generate_img(self, output_path: str) -> bool:
        # A4 plátno – účtenku vykreslíme jako úzký pás uprostřed
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), self._BG)
        d = ImageDraw.Draw(img)

        # Rozměr účtenky (lístku)
        ticket_w = self.mm(80)         # ~80 mm šířka pásky
        ticket_x = (self._A4_W_PX - ticket_w) // 2
        margin_t = self.mm(15)
        y = margin_t
        x0 = ticket_x
        x1 = ticket_x + ticket_w

        # Pomocné čáry
        def hr(ypos:int, weight:str="thin") -> None:
            color = self._LINE if weight == "thin" \
                else (self._LINE_MID if weight == "mid" else self._LINE_STRONG)
            width = 2 if weight in ("thin","mid") else 3
            d.line([(x0, ypos), (x1, ypos)], fill=color, width=width)

        # Horní okraj
        d.rectangle((x0, y, x1, y + self.mm(1)), fill=self._BG)
        y += self.mm(3)

        # --- HLAVIČKA (dynamicky ze supplier) ---
        supplier_name = self._safe(getattr(self.supplier, "name", ""))
        supplier_addr = self._safe(getattr(self.supplier, "address", ""))

        self._draw_center(d, (x0 + x1)//2, y, supplier_name or "—", self._f14b, self._INK)
        y += self.mm(6)
        # Druhý řádek (volitelný, např. „PIZZERIE…“ – použijeme supplier_name znovu, ať je to obecné)
        self._draw_center(d, (x0 + x1)//2, y, supplier_name, self._f10, self._MUTED)
        y += self.mm(5)
        if supplier_addr:
            self._draw_center(d, (x0 + x1)//2, y, supplier_addr, self._f10, self._MUTED)
            y += self.mm(3)
        else:
            y += self.mm(3)
        #IČ, DIČ
        self._draw_center(d, (x0 + x1)//2, y, f"IČ: {self.supplier.register_id}, DIČ: {self.supplier.tax_id}", self._f10, self._MUTED)
        y += self.mm(5)
        hr(y, "thin")
        y += self.mm(3)

        # --- META ÚDAJE ---
        kv_label_x = x0 + self.mm(3)
        kv_val_x = x1 - self.mm(3)

        def kv(label:str, value:str, bold:bool=False) -> None:
            nonlocal y
            d.text((kv_label_x, y), label, font=self._f11, fill=self._INK)
            self._draw_right(d, kv_val_x, y, self._safe(value), self._f11b if bold else self._f11, self._INK)
            y += self.mm(5)

        # mapování na invoice
        kv("Účtenka:", str(self.invoice_number), bold=True)
        kv("Objednávka:", str(self.variable_symbol), bold=True)  # není-li objednávka, použijeme VS
        kv("Datum:", self.issue_date)
        pay_str = self.payment.value if hasattr(self.payment, "value") else self._safe(self.payment)
        kv("Způsob úhrady:", pay_str)
        y += self.mm(2)
        hr(y, "thin")
        y += self.mm(3)

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
            self._draw_center(d, cx, y, txt, font, self._INK)

        th("Název", 0, self._f11b); th("Počet", 1, self._f11b); th("Cena", 2, self._f11b); th("Celkem", 3, self._f11b)
        y += self.mm(6)
        hr(y, "mid")

        def row(name:str, qty:str, price:str, total:str) -> None:
            nonlocal y
            y += self.mm(2.5)
            d.text((col_x[0] + self.mm(2), y), self._safe(name), font=self._f10, fill=self._INK)
            self._draw_center(d, (col_x[1] + col_x[2])//2, y, self._safe(qty), self._f10, self._INK)
            self._draw_right(d, col_x[3] - self.mm(2), y, self._safe(price), self._f10, self._INK)
            self._draw_right(d, col_x[4] - self.mm(2), y, self._safe(total), self._f10, self._INK)
            y += self.mm(6)
            d.line([(x0, y), (x1, y)], fill=self._LINE, width=1)

        # řádky z self.items
        curr = self.currency.value if hasattr(self.currency, "value") else str(self.currency)
        for it in self.items:
            qty = getattr(it, "quantity", None)
            unit = getattr(it, "unit", "ks")
            qty_txt = f"{qty} {unit}" if qty is not None else ""
            if getattr(it, "ppu") is not None:
                ppu_val = it.ppu
            price_txt = f"{self._fmt_money(ppu_val)} {curr}" if ppu_val is not None else ""
            total_txt = f"{self._fmt_money(getattr(it, 'price_with_vat', 0))} {curr}"
            row(getattr(it, "description", ""), qty_txt, price_txt, total_txt)

        y += self.mm(3)

        # --- SOUHRN / TOTALY ---
        kv_label_x = x0 + self.mm(3)
        kv_val_x = x1 - self.mm(3)

        def total_line(label:str, value:str, big:bool=False) -> None:
            nonlocal y
            d.text((kv_label_x, y), label, font=self._f11b if big else self._f11, fill=self._INK)
            self._draw_right(d, kv_val_x, y, value, self._f12b if big else self._f11, self._INK)
            y += self.mm(6 if big else 5)

        # DPH po sazbách (dynamicky z self.vat)
        for v in self.vat:
            total_line(f"Základ ({self._safe(v.vat_percentage)}%)", f"{self._fmt_money(v.vat_base)} {curr}")
            total_line(f"DPH ({self._safe(v.vat_percentage)}%)", f"{self._fmt_money(v.vat)} {curr}")
            hr(y, "thin")
            y += self.mm(2)

        # CELKEM
        hr(y, "mid"); y += self.mm(2.5)
        total_line("Celkem", f"{self._fmt_money(self.calculated_total_price)} {curr}", big=True)

        y += self.mm(3)
        hr(y, "thin")
        y += self.mm(3)

        # --- ZÁKAZNÍK ---
        customer_name = self._safe(getattr(self.customer, "name", ""))
        if customer_name:
            d.text((kv_label_x, y), "Zákazník:", font=self._f11, fill=self._INK)
            self._draw_right(d, kv_val_x, y, customer_name, self._f11b, self._INK)
            y += self.mm(6)

        # --- PATIČKA / POZNÁMKY ---
        y += self.mm(2)
        # „badge“ se způsobem úhrady
        badge_txt = f"Způsob úhrady: {pay_str}"
        w_badge = d.textlength(badge_txt, font=self._f10) + self.mm(6)
        bx0 = max(x0 + self.mm(2), (x0 + x1 - w_badge)//2)
        by0 = y
        by1 = by0 + self.mm(7)
        d.rectangle((bx0, by0, bx0 + w_badge, by1), outline=self._LINE, width=2, fill=None)
        self._draw_center(d, (x0 + x1)//2, by0 + self.mm(1.5), badge_txt, self._f10, self._INK)
        y = by1 + self.mm(4)


        #img.show()
        # Uložení
        self.post_process(img).save(output_path, format="PNG", quality=100, subsampling=0)
        return True