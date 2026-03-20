from typing import Optional, final

from PIL import Image, ImageDraw

from invoice_annotator.utils.GRelationship import GRelationship
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG, SUBTLE_BG, FOOT_BG, BOX_BG, TMOBILE_PINK
from invoices_generator.utility.utils import mm
from invoices_generator.utility.utils import safe, fmt_money


@final
class general_invoice(DInvoice):


    def generate_img(self, output_path: str) -> bool:
        """Generování obecné české faktury """

        # Okraje
        margin_l = mm(20)
        margin_r = mm(20)
        margin_t = mm(20)
        margin_b = mm(20)

        # Vytvoření plátna
        img = Image.new("RGB", (self._A4_W_PX, self._A4_H_PX), BG)
        d = ImageDraw.Draw(img)

        # Pomocná funkce pro obdélníky s pozadím
        def draw_box(x:float, y:float, width:float, height:float, bg_color:Optional[tuple[int,int,int]]=None, border_color:Optional[tuple[int,int,int]]=None, border_width:int=1)->None:
            if bg_color:
                d.rectangle((x, y, x + width, y + height), fill=bg_color)
            if border_color:
                d.rectangle((x, y, x + width, y + height), outline=border_color, width=border_width)

        # Počáteční pozice
        y = margin_t

        # --- HLAVIČKA S OHRANIČENÍM ---
        header_height = mm(120)
        draw_box(margin_l-mm(0), y, self._A4_W_PX - margin_l - margin_r +mm(0), self._A4_H_PX - margin_b - margin_t,
                border_color=LINE, border_width=2)

        # Rozložení na dva sloupce
        left_w = int((self._A4_W_PX - margin_l - margin_r) * 0.48)
        right_x = margin_l + left_w + mm(0)
        right_w = self._A4_W_PX - margin_r - right_x

        # Titulek faktury (vpravo nahoře) - s pozadím
        title_y = y
        title_height = mm(12)
        # draw_box(right_x, title_y, right_w, title_height,
        #          bg_color=BG, border_color=LINE_MID)
        title_center_x = right_x + right_w // 2
        self._draw_center(d, title_center_x, title_y + mm(3.5),
                            label=f"DAŇOVÝ DOKLAD (FAKTURA) č.", text=f"{safe(self.invoice_number)}",
                            font=self._f14b, fill=INK, span_tag=span_tags.INVOICE_NUMBER)

        # Variabilní a konstantní symbol (pod titulkem)
        symbol_y = title_y + title_height + mm(3)
        self._draw_right(d, self._A4_W_PX - margin_r - mm(15), symbol_y,
                            label=f"Variabilní symbol:", text=f"{safe(self.variable_symbol)}", font=self._f10, fill=INK,
                            span_tag=span_tags.VARIABLE_SYMBOL)
        symbol_y += mm(4.5)
        self._draw_right(d, self._A4_W_PX - margin_r - mm(25), symbol_y,
                        label=f"Konstantní symbol:", text=f"{safe(self.const_symbol)}",
                        font=self._f10, fill=INK, span_tag=span_tags.CONST_SYMBOL)

        # Dodavatel (vlevo) - s ohraničením
        supplier_y = y
        supplier_height = mm(30)
        draw_box(margin_l, supplier_y, left_w, supplier_height,
                    border_color=LINE_MID)

        supplier_text_y = supplier_y + mm(5)
        self._text(d,(margin_l + mm(3), supplier_text_y), "Dodavatel:", font=self._f13b, fill=INK)

        self._text(d,(margin_l + mm(30), supplier_text_y), label=f"IČ: ", text=f"{safe(self.supplier.register_id)}",
                font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_REGISTER_ID)

        supplier_text_y += mm(4)

        self._text(d,(margin_l + mm(30), supplier_text_y), label=f"DIČ: ", text=f"{safe(self.supplier.tax_id)}",
                font=self._f11, fill=INK, span_tag=span_tags.SUPPLIER_TAX_ID)
        supplier_text_y += mm(6)

        self._text(d,(margin_l + mm(3), supplier_text_y), f"{safe(self.supplier.name)} {self.supplier.type.value}",
                font=self._f11b, fill=INK)
        supplier_text_y += mm(4)

        if hasattr(self.supplier, 'contact_name'):
            self._text(d,(margin_l + mm(3), supplier_text_y), safe(self.supplier.contact_name),
                font=self._f11, fill=INK)
            supplier_text_y += mm(4)

        self._text(d,(margin_l + mm(3), supplier_text_y), safe(self.supplier.street),
                    font=self._f11, fill=INK)
        supplier_text_y += mm(4)

        if hasattr(self.supplier, 'city'):
            self._text(d,(margin_l + mm(3), supplier_text_y), f"{safe(self.supplier.zip)} {safe(self.supplier.city)}",
                    font=self._f11, fill=INK)
            supplier_text_y += mm(6)

        # Registrační poznámka
        if hasattr(self.supplier, 'registration_note'):
            self._text(d,(margin_l + mm(3), supplier_text_y), safe(self.supplier.registration_note),
                    font=self._f11, fill=INK)

        # Bankovní spojení (vlevo dole)
        bank_y = supplier_y + supplier_height
        bank_height = mm(45)
        draw_box(margin_l + mm(0), bank_y, left_w - mm(0), bank_height,
                    border_color=LINE_MID)

        bank_text_y = bank_y + mm(5)
        self._text(d,(margin_l + mm(3), bank_text_y), "Bankovní spojení:", font=self._f13b, fill=INK)
        bank_text_y += mm(6)

        bank_name = self.bank_account.name
        bic = self.bank_account.BIC
        self._text(d,(margin_l + mm(3), bank_text_y), label=f"Banka / SWIFT: {self.bank_account.name} /", text=f"{bic}",
                font=self._f9, fill=INK, span_tag=span_tags.BIC)
        bank_text_y += mm(4)

        self._text(d,(margin_l + mm(3), bank_text_y), label=f"Číslo účtu: ", text=f"{safe(self.bank_account_number)}",
                font=self._f11, fill=INK, span_tag=span_tags.BANK_ACCOUNT_NUMBER)
        bank_text_y += mm(4)

        self._text(d,(margin_l + mm(3), bank_text_y), label=f"IBAN: ", text=f"{safe(self.IBAN)}",
                font=self._f11, fill=INK, span_tag=span_tags.IBAN)
        bank_text_y += mm(6)

        # Obchodní údaje
        self._text(d,(margin_l + mm(3), bank_text_y), "Obchodní údaje:", font=self._f12b, fill=INK)
        bank_text_y += mm(4)
        self._text(d,(margin_l + mm(3), bank_text_y), f"Zakázka: {safe(getattr(self, 'order_job', ''))}",
                    font=self._f11, fill=INK)
        bank_text_y += mm(3.5)
        self._text(d,(margin_l + mm(3), bank_text_y), f"Objednávka: {safe(getattr(self, 'order_number', ''))}",
                    font=self._f11, fill=INK)
        bank_text_y += mm(3.5)
        self._text(d,(margin_l + mm(3), bank_text_y),
                    label="Dodací list:", text=safe(getattr(self, 'delivery_note', self.invoice_number)),
                    font=self._f11, fill=INK)
        bank_text_y += mm(3.5)
        self._text(d,(margin_l + mm(3), bank_text_y),
                    f"Způsob dopravy: {safe(getattr(self, 'shipping_method', 'Silničně'))}",
                    font=self._f11, fill=INK)

        # Odběratel (vpravo) - s ohraničením
        customer_y = symbol_y + mm(8)
        customer_height = mm(40)
        draw_box(right_x, customer_y, right_w, customer_height, border_color=LINE_MID)

        customer_text_y = customer_y + mm(3)
        self._text(d,(right_x + mm(3), customer_text_y), "Odběratel:", font=self._f13b, fill=INK)
        # customer_text_y += mm(6)

        self._text(d,(right_x + mm(30), customer_text_y), label=f"IČ: ", text=f"{safe(self.customer.register_id)}",
                font=self._f11, fill=INK, span_tag=span_tags.CUSTOMER_REGISTER_ID)
        customer_text_y += mm(4)
        self._text(d,(right_x + mm(30), customer_text_y), label=f"DIČ: ", text=f"{safe(self.customer.tax_id)}",
                font=self._f11, fill=INK, span_tag=span_tags.CUSTOMER_TAX_ID)
        customer_text_y += mm(6)

        self._text(d,(right_x + mm(3), customer_text_y), safe(self.customer.name),
                font=self._f12b, fill=INK)
        customer_text_y += mm(4.5)
        self._text(d,(right_x + mm(3), customer_text_y), safe(self.customer.street),
                font=self._f11, fill=INK)
        customer_text_y += mm(4)

        if hasattr(self.customer, 'city'):
            self._text(d,(right_x + mm(3), customer_text_y), f"{safe(self.customer.zip)} {safe(self.customer.city)}",
                font=self._f11, fill=INK)
            customer_text_y += mm(6)

        # Kontakty
        self._text(d,(right_x + mm(3), customer_text_y), f"Tel.: {safe(getattr(self.customer, 'phone', ''))}",
                font=self._f11, fill=INK)
        customer_text_y += mm(4)
        self._text(d,(right_x + mm(3), customer_text_y), f"Fax: {safe(getattr(self.customer, 'fax', ''))}",
                font=self._f11, fill=INK)
        customer_text_y += mm(4)
        self._text(d,(right_x + mm(3), customer_text_y), f"E-mail: {safe(getattr(self.customer, 'email', ''))}",
                font=self._f11, fill=INK)

        # Datumy (vpravo dole)
        dates_y = customer_y + customer_height

        draw_box(right_x, dates_y, right_w, customer_height, border_color=LINE_MID)

        dates_y += mm(8)

        def date_row(label:str, value:str, bold:bool=False, tag:span_tags = span_tags.O, undersampling:bool=True)->None:
            nonlocal dates_y
            font_val = self._f12b if bold else self._f12
            self._text(d,(right_x + mm(3), dates_y), label, font=self._f11, fill=INK, span_tag=span_tags.O)
            self._draw_right(d, self._A4_W_PX - margin_r - mm(5), dates_y, safe(value),
                            font_val, INK, span_tag=tag)
            dates_y += mm(5.5)

        date_row("Datum splatnosti:", self.due_date, True, span_tags.DUE_DATE)
        date_row("Datum vystavení:", self.issue_date, True, span_tags.ISSUE_DATE)
        date_row("Datum uskutečnění zdanitelného plnění:", self.taxable_supply_date, True, span_tags.TAXABLE_SUPPLY_DATE)

        payment_method = self.payment_type
        date_row("Forma úhrady:", payment_method, True, span_tags.PAYMENT_TYPE)

        # Posun na konec hlavičky
        y = y + header_height

        # --- TABULKA POLOŽEK ---
        table_w = self._A4_W_PX - margin_l - margin_r
        headers = ["Fakturujeme Vám:", "MJ", "Počet MJ", "Cena MJ bez DPH", "DPH", "Sleva", "Celkem bez DPH"]
        col_ws = [0.25, 0.08, 0.12, 0.23, 0.08, 0.08, 0.16]
        col_abs = [int(w * table_w) for w in col_ws]
        x_cols = [margin_l]
        for w in col_abs[:-1]:
            x_cols.append(x_cols[-1] + w)

        # Záhlaví tabulky
        head_h = mm(8)

        # Pozadí záhlaví
        draw_box(margin_l, y, table_w, head_h, bg_color=BG,
                border_color=LINE, border_width=2)

        baseline = y + mm(2.5)

        for i, header_text in enumerate(headers):
            if i == 0:  # První sloupec - vlevo
                self._text(d,(x_cols[i] + 8, baseline), header_text, font=self._f11b, fill=INK, must_have_same_width=True)
            else:  # MJ, DPH, Sleva - na střed
                self._draw_center(d, x_cols[i] + col_abs[i] // 2, baseline, header_text, self._f11b, INK, must_have_same_width=True)

        # Vertikální linky záhlaví
        for i in range(1, len(x_cols)):
            d.line([(x_cols[i], y), (x_cols[i], y + head_h)], fill=LINE_MID, width=1)

        y += head_h

        # Řádky položek
        row_h = mm(7)
        for item in self.items:
            # Ohraničení řádku
            draw_box(margin_l, y, table_w, row_h, border_color=LINE_MID)

            y_text = y + mm(2)

            # Data řádku
            description = safe(getattr(item, 'description', ''))
            unit = safe(getattr(item, 'unit', 't'))
            quantity = safe(getattr(item, 'quantity', ''))
            ppu = fmt_money(getattr(item, 'ppu', getattr(item, 'price_per_unit', 0)))
            vat_percentage = f"{safe(getattr(item, 'vat_percentage', ''))}%"
            discount = safe(getattr(item, 'discount', ''))
            price_without_vat = fmt_money(getattr(item, 'price_without_vat', getattr(item, 'total_price', 0)))

            cells = [description, unit, quantity, ppu, vat_percentage, discount, price_without_vat]

            # Vykreslení buněk
            self._text(d,(x_cols[0] + 8, y_text), cells[0], font=self._f11, fill=INK)
            self._draw_center(d, x_cols[1] + col_abs[1] // 2, y_text, cells[1], self._f11, INK)
            self._draw_right(d, x_cols[2] + col_abs[2] - 8, y_text, cells[2], self._f11, INK)
            self._draw_right(d, x_cols[3] + col_abs[3] - 8, y_text, cells[3], self._f11, INK)
            self._draw_center(d, x_cols[4] + col_abs[4] // 2, y_text, cells[4], self._f11, INK)
            self._draw_center(d, x_cols[5] + col_abs[5] // 2, y_text, cells[5], self._f11, INK)
            self._draw_right(d, x_cols[6] + col_abs[6] - 8, y_text, cells[6], self._f11, INK)

            # Vertikální linky
            for i in range(1, len(x_cols)):
                d.line([(x_cols[i], y), (x_cols[i], y + row_h)], fill=LINE_MID, width=1)

            y += row_h

        # GDPR poznámka (pokud existuje)
        if hasattr(self, 'gdpr_note') and self.gdpr_note:
            draw_box(margin_l, y, table_w, row_h, border_color=LINE_MID)
            y_text = y + mm(2)
            self._text(d,(margin_l + 8, y_text), safe(self.gdpr_note), font=self._f11, fill=INK)
            y += row_h

        # Mezisoučet bez DPH
        y += mm(6)
        currency_text = self.currency.value if hasattr(self.currency, 'value') else str(self.currency)
        total_price = getattr(self, 'calculated_total_price', self.calculated_total_price)
        # Dvouřádkové zobrazení
        self._draw_center(d, self._A4_W_PX - margin_r - mm(30), y,
                        label=f"Celkem k úhradě ({currency_text}):", text=f"{fmt_money(total_price)}", font=self._f12b, fill=INK,
                        span_tag=span_tags.TOTAL)
        y += mm(10)

        # --- ROZPIS DPH A CELKOVÁ ČÁSTKA ---
        left_block_w = int(table_w * 0.60)
        right_block_x = margin_l + left_block_w + mm(5)

        # Rozpis DPH (vlevo) - s záhlavím jako v HTML
        vat_table_height = mm(35)
        # draw_box(margin_l, y, left_block_w, mm(8), border_color=border_color)

        # Nadpis rozpisu
        self._text(d,(margin_l + 8, y + mm(2.5)), "Rozpis DPH v CZK:", font=self._f12b, fill=INK)

        y += mm(8)

        # --- Tabulka rozpisu DPH (generická) ---
        vat_headers = ["Sazba DPH", "Základ DPH", "DPH", "Celkem"]
        vat_col_ws = [0.25, 0.25, 0.25, 0.25]  # stejné šířky sloupců
        vat_col_abs = [int(left_block_w * w) for w in vat_col_ws]
        vat_x_cols = [margin_l]
        for w in vat_col_abs[:-1]:
            vat_x_cols.append(vat_x_cols[-1] + w)

        # Záhlaví
        vat_head_h = mm(6)
        draw_box(margin_l, y, left_block_w, vat_head_h, border_color=LINE_MID)
        vat_y_text = y + mm(1.5)
        for i, header in enumerate(vat_headers):
            # první sloupec zleva, číselné zprava
            if i == 0:
                self._text(d,(vat_x_cols[i] + 6, vat_y_text), header, font=self._f10b, fill=INK)
            else:
                self._draw_right(d, vat_x_cols[i] + vat_col_abs[i] - 6, vat_y_text, header, self._f10b, INK)

        # Svislé linky záhlaví
        for i in range(1, len(vat_x_cols)):
            d.line([(vat_x_cols[i], y), (vat_x_cols[i], y + vat_head_h)], fill=LINE_MID, width=1)

        y += vat_head_h

        # Řádky dle self.vat (libovolný počet sazeb)
        vat_row_h = mm(6)

        for v in self.vat:
            draw_box(margin_l, y, left_block_w, vat_row_h, border_color=LINE_MID)
            vat_y_text = y + mm(1.5)

            # sloupec 0: sazba (můžeš doplnit vlastní label, pokud ho máš v datech)
            _, percentage_id = self._text(d,(vat_x_cols[0] + 6, vat_y_text), text=f"{safe(v.vat_percentage)}",end=" %", font=self._f11, fill=INK,
                        span_tag=span_tags.VAT_PERCENTAGE)

            # sloupec 1: základ
            _, base_id = self._draw_right(d, vat_x_cols[1] + vat_col_abs[1] - 6, vat_y_text,
                        fmt_money(v.vat_base), self._f11, INK, span_tag=span_tags.VAT_BASE, must_have_same_width=True)

            # sloupec 2: DPH
            _, vat_id = self._draw_right(d, vat_x_cols[2] + vat_col_abs[2] - 6, vat_y_text,
                        fmt_money(v.vat), self._f11, INK, span_tag=span_tags.VAT, must_have_same_width=True)

            # sloupec 3: celkem za sazbu (základ + DPH)
            self._draw_right(d, vat_x_cols[3] + vat_col_abs[3] - 6, vat_y_text,
                        fmt_money(float(v.vat_base) + float(v.vat)), self._f11, INK, must_have_same_width=True)

            # svislé linky pro tento řádek
            for i in range(1, len(vat_x_cols)):
                d.line([(vat_x_cols[i], y), (vat_x_cols[i], y + vat_row_h)], fill=LINE_MID, width=1)

            self.append_relationship(GRelationship(None, base_id, percentage_id, relationship_types.BASE_OF))
            self.append_relationship(GRelationship(None, vat_id, percentage_id, relationship_types.VAT_OF))

            y += vat_row_h

        # Součtový řádek
        draw_box(margin_l, y, left_block_w, vat_row_h, border_color=LINE_STRONG, border_width=2)

        vat_y_text = y + mm(1.5)
        self._text(d,(vat_x_cols[0] + 6, vat_y_text), "Součet", font=self._f11b, fill=INK)
        self._draw_right(d, vat_x_cols[3] + vat_col_abs[3] - 6, vat_y_text,
                        fmt_money(self.calculated_total_price), self._f11b, INK, span_tag=span_tags.TOTAL)

        # Vertikální linky
        for i in range(1, len(vat_x_cols)):
            d.line([(vat_x_cols[i], y), (vat_x_cols[i], y + vat_row_h)], fill=LINE_STRONG, width=2)

        # Celková částka k úhradě (vpravo)
        total_y = y - mm(20)
        total_box_w = mm(60)
        total_box_h = mm(15)


        # QR kód placeholder - pod celkovou částkou
        qr_size = mm(22)
        qr_x = right_block_x + (total_box_w - qr_size) // 2
        qr_y = total_y + total_box_h + mm(5)

        draw_box(qr_x, qr_y, qr_size, qr_size, border_color=LINE_MID, border_width=2)
        self._draw_center(d, qr_x + qr_size // 2, qr_y + qr_size // 2, "QR platba", self._f11, (150, 150, 150))

        # --- DOPLŇUJÍCÍ TEXT ---
        y = max(y + mm(15), qr_y + qr_size + mm(10))

        # Doplňující text v boxu jako v HTML
        note_height = mm(5)
        note_text = 'Za každý den prodlení se zaplacením u této faktury, účtujeme úrok z prodlení ve výši 0,05% z dlužné částky'
        self._text(d,(margin_l + 8, y), safe(note_text), font=self._f11, fill=INK)

        y += note_height

        # --- PATIČKA ---
        # Informace o vystaviteli
        issued_by = getattr(self, 'issued_by', 'Světlana Lopatencová')
        supplier_phone = getattr(self.supplier, 'phone', '128 451 231')
        supplier_email = getattr(self.supplier, 'email', 'lopatencova@seznam.cz')

        footer_text = f"Vystavil: {issued_by}     Telefon: {supplier_phone}, E-mail: {supplier_email}"
        self._text(d,(margin_l, y), footer_text, font=self._f11b, fill=INK)

        y += mm(6)

        # Software info - menším písmem, na střed
        software_info = "UJF-SNAKE110074, 6.80.1192, (C) MRP s Informatica, s.r.o., P.O.BOX 35, 783 15 Šluknov"
        self._draw_center(d, self._A4_W_PX // 2, y, software_info, self._f10, INK)

        # img.show()
        img = self.post_process(img)

        # d = ImageDraw.Draw(img)

        # for word in self._words:
        #     d.rectangle(word.b_box, outline=TMOBILE_PINK)
        #     d.text((word.b_box[0], word.b_box[1]+mm(3)),word.tag.value, font=self._f10, fill=TMOBILE_PINK)

        # img.show()

        img.save(output_path, format="PNG")
        return True
