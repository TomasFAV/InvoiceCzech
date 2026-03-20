"""
audi_invoice_full.py

Jeden soubor, který obsahuje:
- generátory polí navíc (VIN, RZ, barva, komise, vyřizuje, telefon, konst. symbol, smlouva)
- (volitelně) logiku plateb: total / paid / due
- třídu audi_invoice s rendererem (PIL) podle tvé šablony

Pozn.:
- Počítá se, že máš k dispozici invoice base class a helpery: mm, safe, fmt_money
- Počítá se, že invoice má fonty self._f.. a metody _text, _draw_right, _draw_center, post_process
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import final

from PIL import Image, ImageDraw

from invoices_generator.core.span import span
from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.enumerates.span_tags import span_tags

from invoices_generator.utility.invoice_consts import INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG
from invoices_generator.utility.utils import mm, safe, fmt_money


# =============================================================================
# GENERÁTORY „NOVÝCH“ POLÍ (co nebyly v Alze)
# =============================================================================

def _digits(n: int) -> str:
    return "".join(random.choice(string.digits) for _ in range(n))


def _upper_alnum(n: int) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def gen_phone_cz() -> str:
    # typický formát "602 356 412"
    a = random.choice([
        "601", "602", "603", "604", "605", "606", "607", "608", "609",
        "720", "721", "722", "723", "724", "725", "726", "727", "728", "729"
    ])
    return f"{a} {_digits(3)} {_digits(3)}"


def gen_const_symbol() -> str:
    # v praxi často 0008, 0308, 0558…
    return random.choice(["0008", "0308", "0558", "1118", "0308", "0001"])


def gen_contract_number() -> str:
    # něco jako "86OA001948"
    return f"{random.choice(['86OA','87OA','85OA','88OA'])}{_digits(6)}"


def gen_commission_number() -> str:
    # něco jako "0146538"
    return _digits(random.choice([6, 7, 8]))


def gen_person_name_cz() -> str:
    first = random.choice([
        "Dana", "Martina", "Petra", "Lucie", "Jana", "Tereza", "Veronika",
        "Petr", "Jan", "Tomáš", "Martin", "David", "Michal", "Lukáš"
    ])
    last = random.choice([
        "Nováková", "Svobodová", "Dvořáková", "Černá", "Procházková", "Krejčí",
        "Novák", "Svoboda", "Dvořák", "Černý", "Procházka", "Krejčí"
    ])
    # občas "Příjmení Jméno"
    if random.random() < 0.35:
        return f"{last} {first}"
    return f"{first} {last}"


def gen_color() -> str:
    # styl jako "A2A2 Černá Brillant"
    code = _upper_alnum(4)
    name = random.choice([
        "Černá Brillant", "Bílá Candy", "Šedá Daytona", "Modrá Navarra",
        "Stříbrná Florett", "Červená Tango", "Zelená District", "Hnědá Teak"
    ])
    return f"{code} {name}"


def gen_rz() -> str:
    # zjednodušený CZ formát: "1AB 2345"
    first = random.choice("123456789")
    letters = "".join(random.choice("ABCDEFGHJKLMNPRSTUVXYZ") for _ in range(2))
    nums = _digits(4)
    return f"{first}{letters} {nums}"


def gen_vin() -> str:
    # VIN = 17 znaků, bez I,O,Q
    alphabet = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    prefix = random.choice(["WAU", "WVW", "TMB", "VF1", "VSS", "WBA", "WDC"])
    rest = "".join(random.choice(alphabet) for _ in range(17 - len(prefix)))
    return prefix + rest


# =============================================================================
# (VOLITELNĚ) LOGIKA PLATEB: total / paid / due
# =============================================================================

@dataclass
class PaymentState:
    total: float
    paid: float
    due: float


def make_payment_state(total: float, fully_paid_prob: float = 0.35, partial_prob: float = 0.15) -> PaymentState:
    """
    total = hodnota faktury (TOTAL)
    paid = kolik bylo uhrazeno
    due  = kolik zbývá (AMOUNT_DUE)
    """
    r = random.random()
    if r < fully_paid_prob:
        return PaymentState(total=total, paid=total, due=0.0)
    if r < fully_paid_prob + partial_prob:
        paid = round(total * random.uniform(0.1, 0.9), 2)
        return PaymentState(total=total, paid=paid, due=round(total - paid, 2))
    return PaymentState(total=total, paid=0.0, due=total)


# =============================================================================
# AUDI TEMPLATE / RENDERER
# =============================================================================

@final
class audi_invoice(DInvoice):
    """
    Šablona podobná:
    - logo Audi vpravo nahoře
    - titul uprostřed: Daňový doklad
    - vpravo nahoře řádek: Číslo dokladu: <...>
    - bloky:
        [Dodavatel]            | [Číslo dokladu / smlouva / konst. symbol + Odběratel]
        [Bankovní spojení]     | [Dodací a platební podmínky]
        [velký prázdný box]    | [velký prázdný box]
    - řádek s údaji o vozidle (VIN, RZ, barva, komise, vyřizuje, telefon)
    - tabulka položek
    - rekapitulace DPH
    - částka k úhradě
    - podpisy + stránkování
    """

    def prepare_audi_fields(self) -> None:
        # pole, co v Alze nebyly
        self.vin = getattr(self, "vin", None) or gen_vin()
        self.license_plate = getattr(self, "license_plate", None) or gen_rz()
        self.vehicle_color = getattr(self, "vehicle_color", None) or gen_color()
        self.commission_number = getattr(self, "commission_number", None) or gen_commission_number()
        self.handler = getattr(self, "handler", None) or gen_person_name_cz()
        self.phone = getattr(self, "phone", None) or gen_phone_cz()

        # meta navíc
        self.constant_symbol = getattr(self, "constant_symbol", None) or gen_const_symbol()
        self.contract_number = getattr(self, "contract_number", None) or gen_contract_number()

        # (volitelné) paid/due – pokud chceš; TOTAL je pořád calculated_total_price
        # Pokud to už máš jinde, klidně tohle smaž.
        total = float(getattr(self, "calculated_total_price", 0) or 0)
        ps = make_payment_state(total)
        self.amount_paid = getattr(self, "amount_paid", None) if hasattr(self, "amount_paid") else ps.paid
        self.amount_due = getattr(self, "amount_due", None) if hasattr(self, "amount_due") else ps.due

    def generate_img(self, output_path: str) -> bool:
        self.prepare_audi_fields()

        # okraje
        margin_l = mm(10)
        margin_r = mm(10)
        margin_t = mm(10)
        margin_b = mm(10)

        W = self._A4_W_PX
        H = self._A4_H_PX

        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)

        # ---------------- helpers ----------------
        def hline(y: int, x0: int, x1: int, weight: str = "mid") -> None:
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            width = 3 if weight == "strong" else (2 if weight == "mid" else 1)
            d.line([(x0, y), (x1, y)], fill=color, width=width)

        def vline(x: int, y0: int, y1: int, weight: str = "mid") -> None:
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            width = 3 if weight == "strong" else (2 if weight == "mid" else 1)
            d.line([(x, y0), (x, y1)], fill=color, width=width)

        def rect(x0: int, y0: int, x1: int, y1: int, weight: str = "mid", fill=None) -> None:
            color = LINE_MID if weight == "mid" else (LINE_STRONG if weight == "strong" else LINE)
            width = 3 if weight == "strong" else (2 if weight == "mid" else 1)
            d.rectangle((x0, y0, x1, y1), outline=color, width=width, fill=fill)

        content_x0 = margin_l
        content_x1 = W - margin_r
        content_w = content_x1 - content_x0

        # =====================================================================
        # TOP: LOGO + TITUL + ČÍSLO DOKLADU
        # =====================================================================
        y = margin_t

        # "Audi" logo vpravo nahoře (text + kroužky)
        logo_x = content_x1 - mm(48)
        logo_y = y

        ring_r = mm(4)
        ring_gap = mm(1.5)
        cx = logo_x + ring_r
        cy = logo_y + ring_r + mm(1)
        for _ in range(4):
            d.ellipse((cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r), outline=INK, width=2)
            cx += (2 * ring_r - ring_gap)

        self._text(d, (logo_x + mm(8), logo_y + mm(12)), "Audi", font=self._f14b, fill=(200, 0, 0))

        # titul uprostřed
        self._draw_center(d, W / 2, y + mm(16), "Daňový doklad", self._f16b, INK)

        # řádek číslo dokladu vpravo
        doc_no = safe(getattr(self, "invoice_number", getattr(self, "document_number", "")))
        self._draw_right(
            d,
            content_x1,
            y + mm(22),
            label="Číslo dokladu:",
            text=f"{doc_no}",
            font=self._f11b,
            fill=INK,
            span_tag=span_tags.INVOICE_NUMBER
        )

        y += mm(30)

        # =====================================================================
        # BLOKY (2 sloupce, 2 řádky)
        # =====================================================================
        gap_x = mm(8)
        col_w = int((content_w - gap_x) / 2)

        left_x0 = content_x0
        left_x1 = left_x0 + col_w
        right_x0 = left_x1 + gap_x
        right_x1 = content_x1

        row1_h = mm(52)
        rect(left_x0, y, left_x1, y + row1_h, weight="mid")
        rect(right_x0, y, right_x1, y + row1_h, weight="mid")

        pad = mm(4)

        # LEFT: Dodavatel
        cur = y + pad
        self._text(d, (left_x0 + pad, cur), "Dodavatel", font=self._f11b, fill=INK)
        hline(cur + mm(4.5), left_x0 + pad, left_x1 - pad, "thin")
        cur += mm(7)

        self._text(d, (left_x0 + pad, cur), safe(self.supplier.name), font=self._f10, fill=INK)
        cur += mm(5)
        self._text(d, (left_x0 + pad, cur), safe(self.supplier.address), font=self._f10, fill=INK)
        cur += mm(5)

        self._text(d, (left_x0 + pad, cur), "IČ:", font=self._f10, fill=INK)
        self._text(d, (left_x0 + pad + mm(40), cur), safe(self.supplier.register_id),
                   font=self._f10b, fill=INK, span_tag=span_tags.SUPPLIER_REGISTER_ID)
        self._text(d, (left_x0 + pad, cur+mm(10)), "DIČ:", font=self._f10, fill=INK)
        self._text(d, (left_x0 + pad + mm(40), cur+mm(10)), safe(self.supplier.tax_id),
                   font=self._f10b, fill=INK, span_tag=span_tags.SUPPLIER_TAX_ID)

        # RIGHT: meta + odběratel
        cur = y + pad
        meta_h = mm(18)
        rect(right_x0 + pad, cur, right_x1 - pad, cur + meta_h, weight="thin")

        mx0 = right_x0 + pad + mm(3)
        my = cur + mm(2.5)
        mvx = right_x1 - pad - mm(3)

        def meta_row(label: str, value: str, tag: span_tags = span_tags.O) -> None:
            nonlocal my
            self._text(d, (mx0, my), label, font=self._f9, fill=INK)
            self._draw_right(d, mvx, my, safe(value), self._f9b, INK, span_tag=tag)
            my += mm(4.8)

        meta_row("Číslo dokladu:    (var. symbol)", doc_no, span_tags.VARIABLE_SYMBOL)
        meta_row("Smlouva-objednávka:", safe(self.contract_number))
        meta_row("Konstantní symbol:", safe(self.constant_symbol), span_tags.CONST_SYMBOL)

        cust_y0 = y + pad + meta_h + mm(4)
        cust_y1 = y + row1_h - pad
        rect(right_x0 + pad, cust_y0, right_x1 - pad, cust_y1, weight="thin")

        cx0 = right_x0 + pad + mm(3)
        cy = cust_y0 + mm(2.5)
        self._text(d, (cx0, cy), "Odběratel", font=self._f10b, fill=INK)
        cy += mm(5.5)

        cust_id = safe(getattr(self.customer, "customer_id", getattr(self, "customer_id", "")))
        if cust_id:
            self._text(d, (cx0, cy), cust_id, font=self._f9b, fill=INK)
            cy += mm(4.8)

        self._text(d, (cx0, cy), safe(self.customer.name), font=self._f10b, fill=INK)
        cy += mm(4.8)
        self._text(d, (cx0, cy), safe(self.customer.address), font=self._f10, fill=INK)

        cy += mm(5)

        self._text(d, (cx0, cy), "IČ/RČ:", font=self._f9, fill=INK)
        self._text(d, (cx0 + mm(34), cy), safe(self.customer.register_id),
                   font=self._f9b, fill=INK, span_tag=span_tags.CUSTOMER_REGISTER_ID)
        
        cy += mm(5)
        
        self._text(d, (cx0, cy), "DIČ:", font=self._f9, fill=INK)
        self._text(d, (cx0 + mm(34), cy), safe(self.customer.tax_id),
                   font=self._f9b, fill=INK, span_tag=span_tags.CUSTOMER_TAX_ID)

        y += row1_h + mm(6)

        # ---- row 2: Bankovní spojení | Dodací a platební podmínky
        row2_h = mm(40)
        rect(left_x0, y, left_x1, y + row2_h, weight="mid")
        rect(right_x0, y, right_x1, y + row2_h, weight="mid")

        # LEFT
        cur = y + pad
        self._text(d, (left_x0 + pad, cur), "Bankovní spojení", font=self._f11b, fill=INK)
        bank_name = safe(getattr(self.bank_account, "name", getattr(self, "bank_name", ""))) if getattr(self, "bank_account", None) else safe(getattr(self, "bank_name", ""))
        if bank_name:
            self._draw_right(d, left_x1 - pad, cur, bank_name, self._f10, INK)
        hline(cur + mm(4.5), left_x0 + pad, left_x1 - pad, "thin")
        cur += mm(7)

        acct = safe(getattr(self, "bank_account_number", ""))
        iban = safe(getattr(self, "IBAN", ""))
        bic = safe(getattr(self.bank_account, "BIC", "")) if getattr(self, "bank_account", None) else safe(getattr(self, "bic", ""))

        self._text(d, (left_x0 + pad, cur), acct, font=self._f10, fill=INK,
                   span_tag=span_tags.BANK_ACCOUNT_NUMBER)
        cur += mm(5)
        self._text(d, (left_x0 + pad, cur), "IBAN:", font=self._f10, fill=INK)
        self._text(d, (left_x0 + pad + mm(44), cur), iban, font=self._f10, fill=INK,
                   span_tag=span_tags.IBAN)
        cur += mm(5)
        self._text(d, (left_x0 + pad, cur), "SWIFT:", font=self._f10, fill=INK)
        self._text(d, (left_x0 + pad + mm(44), cur), bic, font=self._f10, fill=INK,
                   span_tag=span_tags.BIC)

        # RIGHT
        cur = y + pad
        self._text(d, (right_x0 + pad, cur), "Dodací a platební podmínky", font=self._f11b, fill=INK)
        hline(cur + mm(4.5), right_x0 + pad, right_x1 - pad, "thin")
        cur += mm(7)

        def cond_row(label: str, value: str, tag: span_tags = span_tags.O) -> None:
            nonlocal cur
            self._text(d, (right_x0 + pad, cur), label, font=self._f10, fill=INK)
            self._text(d, (right_x0 + mm(60), cur), safe(value), font=self._f10, fill=INK,
                       span_tag=tag)
            cur += mm(5)

        cond_row("Datum vystavení:", safe(getattr(self, "issue_date", "")), span_tags.ISSUE_DATE)
        cond_row("Datum splatnosti:", safe(getattr(self, "due_date", "")), span_tags.DUE_DATE)
        cond_row("Datum DUZP:", safe(getattr(self, "taxable_supply_date", getattr(self, "issue_date", ""))), span_tags.TAXABLE_SUPPLY_DATE)
        pay = safe(self.payment_type)
        cond_row("Forma úhrady:", pay, span_tags.PAYMENT_TYPE)

        y += row2_h + mm(8)

        # =====================================================================
        # ŘÁDEK: údaje o vozidle
        # =====================================================================
        veh_h = mm(16)
        rect(content_x0, y, content_x1, y + veh_h, weight="mid")

        segs = [0.22, 0.14, 0.08, 0.22, 0.12, 0.14, 0.08]
        xs = [content_x0]
        for f in segs[:-1]:
            xs.append(xs[-1] + int(content_w * f))
        for x in xs[1:]:
            vline(x, y, y + veh_h, "thin")

        vy = y + mm(3.2)

        self._text(d, (xs[0] + mm(2), vy), "Číslo karoserie:", self._f9, INK)
        self._text(d, (xs[0] + mm(20), vy), safe(self.vin), self._f8, INK,
                   span_tag=span_tags.VIN if hasattr(span_tags, "VIN") else span_tags.O)

        self._text(d, (xs[1] + mm(2), vy), "Tech. průkaz:", self._f9, INK)

        self._text(d, (xs[2] + mm(2), vy), "RZ:", self._f9, INK)
        self._text(d, (xs[2] + mm(7), vy), safe(self.license_plate), self._f8, INK,
                   span_tag=span_tags.LICENSE_PLATE if hasattr(span_tags, "LICENSE_PLATE") else span_tags.O)

        self._text(d, (xs[3] + mm(2), vy), "Barva:", self._f9, INK)
        self._text(d, (xs[3] + mm(14), vy), safe(self.vehicle_color), self._f9b, INK)

        self._text(d, (xs[4] + mm(2), vy), "Číslo komise:", self._f9, INK)

        self._text(d, (xs[5] + mm(2), vy), "Vyřizuje:", self._f9, INK)
        self._text(d, (xs[5] + mm(10), vy), safe(self.handler), self._f9b, INK)

        self._text(d, (xs[6] + mm(2), vy), "Telefon:", self._f9, INK)   

        y += veh_h + mm(8)

        # =====================================================================
        # TABULKA POLOŽEK
        # =====================================================================
        self._text(d, (content_x0, y), "Fakturujeme Vám přihlášení vozu", font=self._f10, fill=INK)
        y += mm(6)

        headers = ["Název", "Množství mj", "Základ/mj", "Zákl. DPH", "% DPH", "DPH", "Celkem vč. DPH"]
        fr =      [0.20,    0.17,          0.12,        0.12,      0.13,  0.13,  0.13]
        col_ws = [int(content_w * f) for f in fr]
        xs = [content_x0]
        for w_ in col_ws[:-1]:
            xs.append(xs[-1] + w_)

        hline(y, content_x0, content_x1, "strong")
        y += mm(2)

        for i, h in enumerate(headers):
            if i == 0:
                self._text(d, (xs[i] + mm(2), y), h, self._f10b, INK, must_have_same_width=True)
            else:
                self._draw_right(d, xs[i] + col_ws[i] - mm(2), y, h, self._f10b, INK, must_have_same_width=True)

        y += mm(6)
        hline(y, content_x0, content_x1, "thin")
        y += mm(2)

        row_h = mm(6)
        max_rows = min(len(self.items), 6)

        for i in range(max_rows):
            it = self.items[i]
            name = safe(getattr(it, "description", getattr(it, "name", "")))
            qty = safe(getattr(it, "quantity", "1,00"))
            base_mj = fmt_money(getattr(it, "ppu", getattr(it, "unit_price", 0)))
            base = fmt_money(getattr(it, "price_without_vat", getattr(it, "vat_base", 0)))
            vatp = safe(getattr(it, "vat_percentage", "21,00"))
            vat = fmt_money(getattr(it, "vat", 0))
            total = fmt_money(getattr(it, "price_with_vat", getattr(it, "total", 0)))

            self._text(d, (xs[0] + mm(2), y), name, self._f10, INK)
            self._draw_right(d, xs[1] + col_ws[1] - mm(2), y, qty, self._f10, INK)
            self._draw_right(d, xs[2] + col_ws[2] - mm(2), y, base_mj, self._f10, INK)
            self._draw_right(d, xs[3] + col_ws[3] - mm(2), y, base, self._f10, INK,
                             span_tag=span_tags.VAT_BASE)
            self._draw_right(d, xs[4] + col_ws[4] - mm(2), y, vatp, self._f10, INK,
                             span_tag=span_tags.VAT_PERCENTAGE)
            self._draw_right(d, xs[5] + col_ws[5] - mm(2), y, vat, self._f10, INK,
                             span_tag=span_tags.VAT)
            self._draw_right(d, xs[6] + col_ws[6] - mm(2), y, total, self._f10, INK)

            y += row_h
            hline(y, content_x0, content_x1, "thin")
            y += mm(2)

        y += mm(8)

        # =====================================================================
        # REKAPITULACE DPH
        # =====================================================================
        recap_w = int(content_w)
        rx0 = content_x0
        rx1 = rx0 + recap_w
        ry0 = y
        recap_h = mm(24) + mm(6) * max(2, len(getattr(self, "vat", [])))
        rect(rx0, ry0, rx1, ry0 + recap_h, "mid")

        self._text(d, (rx0 + mm(2), ry0 + mm(2)), "Rekapitulace DPH", self._f10b, INK)

        cols = ["Sazba DPH", "Základ daně", "DPH", "Celkem"]
        cfr = [0.25, 0.27, 0.24, 0.24]
        cws = [int(recap_w * f) for f in cfr]
        cxs = [rx0]
        for w_ in cws[:-1]:
            cxs.append(cxs[-1] + w_)

        header_y = ry0 + mm(8)
        hline(header_y + mm(5), rx0, rx1, "thin")
        for i, c in enumerate(cols):
            if i == 0:
                self._text(d, (cxs[0] + cws[0] - mm(20), header_y), text=c,font=self._f9,fill=INK)
            else:
                self._text(d, (cxs[i] + cws[i] - mm(20), header_y), c, self._f9b, INK)

        row_y = header_y + mm(7)
        for v in getattr(self, "vat", [])[:3]:
            perc = safe(getattr(v, "vat_percentage", ""))
            base = fmt_money(getattr(v, "vat_base", 0))
            vatv = fmt_money(getattr(v, "vat", 0))
            tot = fmt_money(getattr(v, "total_with_vat", getattr(v, "price_with_vat", 0)))

            self._text(d, (cxs[0] + cws[0] - mm(20), row_y), f"{perc} %", self._f9, INK,
                             span_tag=span_tags.VAT_PERCENTAGE)
            self._text(d, (cxs[1] + cws[1] - mm(20), row_y), base, self._f9, INK,
                             span_tag=span_tags.VAT_BASE)
            self._text(d, (cxs[2] + cws[2] - mm(20), row_y), vatv, self._f9, INK,
                             span_tag=span_tags.VAT)
            self._text(d, (cxs[3] + cws[3] - mm(20), row_y), tot, self._f9, INK)
            row_y += mm(6)

        y = ry0 + recap_h + mm(10)


        # =====================================================================
        # PODPISY + FOOTER
        # =====================================================================
        sig_y = H - margin_b 
        hline(sig_y + mm(18), content_x0, content_x0 + int(content_w * 0.40), "thin")
        hline(sig_y + mm(18), content_x0 + int(content_w * 0.55), content_x1, "thin")

        self._text(d, (content_x0, sig_y), "Fakturu převzal:", self._f10, INK)

        issuer = safe(getattr(self, "issuer", getattr(self, "handler", "")))
        self._text(d, (content_x0 + int(content_w * 0.45), sig_y), "Fakturoval:", self._f10, INK)
        self._text(d, (content_x0 + int(content_w * 0.57), sig_y), issuer, self._f10, INK)

        self._draw_center(d, content_x0 + int(content_w * 0.20), sig_y + mm(20), "Zákazník", self._f10, INK)
        self._draw_center(d, content_x0 + int(content_w * 0.78), sig_y + mm(20), safe(self.supplier.name), self._f10, INK)

        self._draw_center(d, W / 2, H - margin_b - mm(8), "Strana 1 / 2", self._f9, INK)
        self._draw_right(d, content_x1, H - margin_b - mm(8), safe(getattr(self, "print_id", "ID tisku 1302710")), self._f9, INK)

        img = self.post_process(img)
        img.save(output_path, format="PNG")
        return True
