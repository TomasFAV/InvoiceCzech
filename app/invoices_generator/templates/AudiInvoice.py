from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import final

from PIL import Image, ImageDraw

from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.renderers.TextRenderer import TextRenderer
from common.invoice.models.InvoiceTemplate import InvoiceTemplate

from common.enumerates.SpanTag import SpanTag
from common.utils.consts import _A4_H_PX, _A4_W_PX, INK, MUTED, LINE, LINE_MID, LINE_STRONG, BG
from common.utils.utilities import mm, safe, fmt_money


# =============================================================================
# GENERÁTORY DOPLŇKOVÝCH POLÍ
# =============================================================================

def _digits(n: int) -> str:
    return "".join(random.choice(string.digits) for _ in range(n))


def _upper_alnum(n: int) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def gen_phone_cz() -> str:
    a = random.choice([
        "601", "602", "603", "604", "605", "606", "607", "608", "609",
        "720", "721", "722", "723", "724", "725", "726", "727", "728", "729"
    ])
    return f"{a} {_digits(3)} {_digits(3)}"


def gen_contract_number() -> str:
    return f"{random.choice(['86OA', '87OA', '85OA', '88OA'])}{_digits(6)}"


def gen_commission_number() -> str:
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
    return f"{last} {first}" if random.random() < 0.35 else f"{first} {last}"


def gen_color() -> str:
    code = _upper_alnum(4)
    name = random.choice([
        "Černá Brillant", "Bílá Candy", "Šedá Daytona", "Modrá Navarra",
        "Stříbrná Florett", "Červená Tango", "Zelená District", "Hnědá Teak"
    ])
    return f"{code} {name}"


def gen_rz() -> str:
    first = random.choice("123456789")
    letters = "".join(random.choice("ABCDEFGHJKLMNPRSTUVXYZ") for _ in range(2))
    nums = _digits(4)
    return f"{first}{letters} {nums}"


def gen_vin() -> str:
    alphabet = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    prefix = random.choice(["WAU", "WVW", "TMB", "VF1", "VSS", "WBA", "WDC"])
    rest = "".join(random.choice(alphabet) for _ in range(17 - len(prefix)))
    return prefix + rest


# =============================================================================
# PLATEBNÍ STAV
# =============================================================================

@dataclass
class PaymentState:
    total: float
    paid: float
    due: float


def make_payment_state(total: float, fully_paid_prob: float = 0.35, partial_prob: float = 0.15) -> PaymentState:
    r = random.random()
    if r < fully_paid_prob:
        return PaymentState(total=total, paid=total, due=0.0)
    if r < fully_paid_prob + partial_prob:
        paid = round(total * random.uniform(0.1, 0.9), 2)
        return PaymentState(total=total, paid=paid, due=round(total - paid, 2))
    return PaymentState(total=total, paid=0.0, due=total)


# =============================================================================
# AUDI TEMPLATE
# =============================================================================

@final
class AudiInvoice(InvoiceTemplate):

    @staticmethod
    def prepare_audi_fields(data: InvoiceData) -> None:
        data.vin = getattr(data, "vin", None) or gen_vin()
        data.license_plate = getattr(data, "license_plate", None) or gen_rz()
        data.vehicle_color = getattr(data, "vehicle_color", None) or gen_color()
        data.commission_number = getattr(data, "commission_number", None) or gen_commission_number()
        data.handler = getattr(data, "handler", None) or gen_person_name_cz()
        data.phone = getattr(data, "phone", None) or gen_phone_cz()

        data.constant_symbol = getattr(data, "const_symbol", None)
        data.contract_number = getattr(data, "contract_number", None) or gen_contract_number()

        total = float(getattr(data, "calculated_total_price", 0) or 0)
        ps = make_payment_state(total)

        if not hasattr(data, "amount_paid") or getattr(data, "amount_paid", None) is None:
            data.amount_paid = ps.paid
        if not hasattr(data, "amount_due") or getattr(data, "amount_due", None) is None:
            data.amount_due = ps.due

    @staticmethod
    def render(textRenderer: TextRenderer, data: InvoiceData, invoice: Invoice) -> bool:
        AudiInvoice.prepare_audi_fields(data)

        margin_l = mm(10)
        margin_r = mm(10)
        margin_t = mm(10)
        margin_b = mm(10)

        img = Image.new("RGB", (_A4_W_PX, _A4_H_PX), BG)
        invoice.image = img
        d = ImageDraw.Draw(img)

        content_x0 = margin_l
        content_x1 = _A4_W_PX - margin_r
        content_w = content_x1 - content_x0

        def hline(y: int, x0: int | None = None, x1: int | None = None, weight: str = "mid") -> None:
            x0 = content_x0 if x0 is None else x0
            x1 = content_x1 if x1 is None else x1
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

        y = margin_t

        # =====================================================================
        # HLAVIČKA
        # =====================================================================

        logo_x = content_x1 - mm(48)
        logo_y = y

        ring_r = mm(4)
        ring_gap = mm(1.5)
        cx = logo_x + ring_r
        cy = logo_y + ring_r + mm(1)
        for _ in range(4):
            d.ellipse((cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r), outline=INK, width=2)
            cx += (2 * ring_r - ring_gap)

        textRenderer._text(invoice, (logo_x + mm(8), logo_y + mm(12)), "Audi", font=textRenderer._f14b, fill=(200, 0, 0))

        title_center_x = _A4_W_PX // 2
        textRenderer._text_center(invoice, title_center_x, y + mm(16), "Daňový doklad", textRenderer._f16b, INK)

        doc_no = safe(getattr(data, "invoice_number", getattr(data, "document_number", "")))
        textRenderer._text_right(
            invoice,
            content_x1,
            y + mm(22),
            text=doc_no,
            font=textRenderer._f11b,
            fill=INK,
            label="Číslo dokladu:",
            span_tag=SpanTag.INVOICE_NUMBER,
        )

        y += mm(30)

        # =====================================================================
        # 2x2 BLOKY
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
        textRenderer._text(invoice, (left_x0 + pad, cur), "Dodavatel", font=textRenderer._f11b, fill=INK)
        hline(cur + mm(4.5), left_x0 + pad, left_x1 - pad, "thin")
        cur += mm(7)

        textRenderer._text(invoice, (left_x0 + pad, cur), safe(data.supplier.name), font=textRenderer._f10, fill=INK)
        cur += mm(5)
        textRenderer._text(invoice, (left_x0 + pad, cur), safe(data.supplier.address), font=textRenderer._f10, fill=INK)
        cur += mm(5)

        textRenderer._text(invoice, (left_x0 + pad, cur), "IČ:", font=textRenderer._f10, fill=INK)
        textRenderer._text(
            invoice,    
            (left_x0 + pad + mm(40), cur),
            safe(data.supplier.register_id),
            font=textRenderer._f10b,
            fill=INK,
            span_tag=SpanTag.SUPPLIER_REGISTER_ID,
        )

        textRenderer._text(invoice, (left_x0 + pad, cur + mm(10)), "DIČ:", font=textRenderer._f10, fill=INK)
        textRenderer._text(
            invoice,
            (left_x0 + pad + mm(40), cur + mm(10)),
            safe(data.supplier.tax_id),
            font=textRenderer._f10b,
            fill=INK,
            span_tag=SpanTag.SUPPLIER_TAX_ID,
        )

        # RIGHT: meta + odběratel
        cur = y + pad
        meta_h = mm(18)
        rect(right_x0 + pad, cur, right_x1 - pad, cur + meta_h, weight="thin")

        mx0 = right_x0 + pad + mm(3)
        my = cur + mm(2.5)
        mvx = right_x1 - pad - mm(3)

        def meta_row(label: str, value: str, tag: SpanTag = SpanTag.O) -> None:
            nonlocal my
            textRenderer._text(invoice, (mx0, my), label, font=textRenderer._f9, fill=INK)
            textRenderer._text_right(invoice, mvx, my, safe(value), textRenderer._f9b, INK, span_tag=tag)
            my += mm(4.8)

        meta_row("Číslo dokladu:    (var. symbol)", doc_no, SpanTag.VARIABLE_SYMBOL)
        meta_row("Smlouva-objednávka:", safe(getattr(data, "contract_number", "")))
        meta_row("Konstantní symbol:", safe(getattr(data, "constant_symbol", "")), SpanTag.CONST_SYMBOL)

        cust_y0 = y + pad + meta_h + mm(4)
        cust_y1 = y + row1_h - pad
        rect(right_x0 + pad, cust_y0, right_x1 - pad, cust_y1, weight="thin")

        cx0 = right_x0 + pad + mm(3)
        cy = cust_y0 + mm(2.5)

        textRenderer._text(invoice, (cx0, cy), "Odběratel", font=textRenderer._f10b, fill=INK)
        cy += mm(5.5)

        cust_id = safe(getattr(data.customer, "customer_id", getattr(data, "customer_id", "")))
        if cust_id:
            textRenderer._text(invoice, (cx0, cy), cust_id, font=textRenderer._f9b, fill=INK)
            cy += mm(4.8)

        textRenderer._text(invoice, (cx0, cy), safe(data.customer.name), font=textRenderer._f10b, fill=INK)
        cy += mm(4.8)
        textRenderer._text(invoice, (cx0, cy), safe(data.customer.address), font=textRenderer._f10, fill=INK)

        cy += mm(5)
        textRenderer._text(invoice, (cx0, cy), "IČ/RČ:", font=textRenderer._f9, fill=INK)
        textRenderer._text(
            invoice,
            (cx0 + mm(34), cy),
            safe(data.customer.register_id),
            font=textRenderer._f9b,
            fill=INK,
            span_tag=SpanTag.CUSTOMER_REGISTER_ID,
        )

        cy += mm(5)
        textRenderer._text(invoice, (cx0, cy), "DIČ:", font=textRenderer._f9, fill=INK)
        textRenderer._text(
            invoice,
            (cx0 + mm(34), cy),
            safe(data.customer.tax_id),
            font=textRenderer._f9b,
            fill=INK,
            span_tag=SpanTag.CUSTOMER_TAX_ID,
        )

        y += row1_h + mm(6)

        # =====================================================================
        # BANKA + PODMÍNKY
        # =====================================================================

        row2_h = mm(40)
        rect(left_x0, y, left_x1, y + row2_h, weight="mid")
        rect(right_x0, y, right_x1, y + row2_h, weight="mid")

        # LEFT
        cur = y + pad
        textRenderer._text(invoice, (left_x0 + pad, cur), "Bankovní spojení", font=textRenderer._f11b, fill=INK)

        bank_name = (
            safe(getattr(data.bank_account, "name", ""))
            if getattr(data, "bank_account", None)
            else safe(getattr(data, "bank_name", ""))
        )
        if bank_name:
            textRenderer._text_right(invoice, left_x1 - pad, cur, bank_name, textRenderer._f10, INK)

        hline(cur + mm(4.5), left_x0 + pad, left_x1 - pad, "thin")
        cur += mm(7)

        acct = safe(getattr(data, "bank_account_number", ""))
        iban = safe(getattr(data, "IBAN", ""))
        bic = (
            safe(getattr(data.bank_account, "BIC", ""))
            if getattr(data, "bank_account", None)
            else safe(getattr(data, "bic", ""))
        )

        textRenderer._text(
            invoice,
            (left_x0 + pad, cur),
            acct,
            font=textRenderer._f10,
            fill=INK,
            span_tag=SpanTag.BANK_ACCOUNT_NUMBER,
        )
        cur += mm(5)

        textRenderer._text(invoice, (left_x0 + pad, cur), "IBAN:", font=textRenderer._f10, fill=INK)
        textRenderer._text(
            invoice,
            (left_x0 + pad + mm(44), cur),
            iban,
            font=textRenderer._f10,
            fill=INK,
            span_tag=SpanTag.IBAN,
        )
        cur += mm(5)

        textRenderer._text(invoice, (left_x0 + pad, cur), "SWIFT:", font=textRenderer._f10, fill=INK)
        textRenderer._text(
            invoice,
            (left_x0 + pad + mm(44), cur),
            bic,
            font=textRenderer._f10,
            fill=INK,
            span_tag=SpanTag.BIC,
        )

        # RIGHT
        cur = y + pad
        textRenderer._text(invoice, (right_x0 + pad, cur), "Dodací a platební podmínky", font=textRenderer._f11b, fill=INK)
        hline(cur + mm(4.5), right_x0 + pad, right_x1 - pad, "thin")
        cur += mm(7)

        def cond_row(label: str, value: str, tag: SpanTag = SpanTag.O) -> None:
            nonlocal cur
            textRenderer._text(invoice, (right_x0 + pad, cur), label, font=textRenderer._f10, fill=INK)
            textRenderer._text(
                invoice,
                (right_x0 + mm(60), cur),
                safe(value),
                font=textRenderer._f10,
                fill=INK,
                span_tag=tag,
            )
            cur += mm(5)

        cond_row("Datum vystavení:", safe(getattr(data, "issue_date", "")), SpanTag.ISSUE_DATE)
        cond_row("Datum splatnosti:", safe(getattr(data, "due_date", "")), SpanTag.DUE_DATE)
        cond_row(
            "Datum DUZP:",
            safe(getattr(data, "taxable_supply_date", getattr(data, "issue_date", ""))),
            SpanTag.TAXABLE_SUPPLY_DATE,
        )
        cond_row("Forma úhrady:", safe(getattr(data, "payment_type", "")), SpanTag.PAYMENT_TYPE)

        y += row2_h + mm(8)

        # =====================================================================
        # ÚDAJE O VOZIDLE
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

        textRenderer._text(invoice, (xs[0] + mm(2), vy), "Číslo karoserie:", textRenderer._f9, INK)
        textRenderer._text(
            invoice,
            (xs[0] + mm(20), vy),
            safe(getattr(data, "vin", "")),
            textRenderer._f8,
            INK,
            span_tag=SpanTag.VIN if hasattr(SpanTag, "VIN") else SpanTag.O,
        )

        textRenderer._text(invoice, (xs[1] + mm(2), vy), "Tech. průkaz:", textRenderer._f9, INK)

        textRenderer._text(invoice, (xs[2] + mm(2), vy), "RZ:", textRenderer._f9, INK)
        textRenderer._text(
            invoice,
            (xs[2] + mm(7), vy),
            safe(getattr(data, "license_plate", "")),
            textRenderer._f8,
            INK,
            span_tag=SpanTag.LICENSE_PLATE if hasattr(SpanTag, "LICENSE_PLATE") else SpanTag.O,
        )

        textRenderer._text(invoice, (xs[3] + mm(2), vy), "Barva:", textRenderer._f9, INK)
        textRenderer._text(
            invoice,
            (xs[3] + mm(14), vy),
            safe(getattr(data, "vehicle_color", "")),
            textRenderer._f9b,
            INK,
        )

        textRenderer._text(invoice, (xs[4] + mm(2), vy), "Číslo komise:", textRenderer._f9, INK)
        textRenderer._text(
            invoice,
            (xs[4] + mm(20), vy),
            safe(getattr(data, "commission_number", "")),
            textRenderer._f8,
            INK,
        )

        textRenderer._text(invoice, (xs[5] + mm(2), vy), "Vyřizuje:", textRenderer._f9, INK)
        textRenderer._text(
            invoice,
            (xs[5] + mm(10), vy),
            safe(getattr(data, "handler", "")),
            textRenderer._f9b,
            INK,
        )

        textRenderer._text(invoice, (xs[6] + mm(2), vy), "Telefon:", textRenderer._f9, INK)
        textRenderer._text(
            invoice,
            (xs[6] + mm(11), vy),
            safe(getattr(data, "phone", "")),
            textRenderer._f8,
            INK,
        )

        y += veh_h + mm(8)

        # =====================================================================
        # TABULKA POLOŽEK
        # =====================================================================

        textRenderer._text(invoice, (content_x0, y), "Fakturujeme Vám přihlášení vozu", font=textRenderer._f10, fill=INK)
        y += mm(6)

        headers = ["Název", "Množství mj", "Základ/mj", "Zákl. DPH", "% DPH", "DPH", "Celkem vč. DPH"]
        fr = [0.20, 0.17, 0.12, 0.12, 0.13, 0.13, 0.13]
        col_ws = [int(content_w * f) for f in fr]
        xs = [content_x0]
        for w_ in col_ws[:-1]:
            xs.append(xs[-1] + w_)

        hline(y, content_x0, content_x1, "strong")
        y += mm(2)

        for i, h in enumerate(headers):
            if i == 0:
                textRenderer._text(
                    invoice,
                    (xs[i] + mm(2), y),
                    h,
                    font=textRenderer._f10b,
                    fill=INK,
                    must_have_same_width=True,
                )
            else:
                textRenderer._text_right(
                    invoice,
                    xs[i] + col_ws[i] - mm(2),
                    y,
                    h,
                    textRenderer._f10b,
                    INK,
                    must_have_same_width=True,
                )

        y += mm(6)
        hline(y, content_x0, content_x1, "thin")
        y += mm(2)

        row_h = mm(6)
        max_rows = min(len(data.items), 6)

        for i in range(max_rows):
            it = data.items[i]
            name = safe(getattr(it, "description", getattr(it, "name", "")))
            qty = safe(getattr(it, "quantity", "1,00"))
            base_mj = fmt_money(getattr(it, "ppu", getattr(it, "unit_price", 0)))
            base = fmt_money(getattr(it, "price_without_vat", getattr(it, "vat_base", 0)))
            vatp = safe(getattr(it, "vat_percentage", "21,00"))
            vat = fmt_money(getattr(it, "vat", 0))
            total = fmt_money(getattr(it, "price_with_vat", getattr(it, "total", 0)))

            textRenderer._text(invoice, (xs[0] + mm(2), y), name, textRenderer._f10, INK)
            textRenderer._text_right(invoice, xs[1] + col_ws[1] - mm(2), y, qty, textRenderer._f10, INK)
            textRenderer._text_right(invoice, xs[2] + col_ws[2] - mm(2), y, base_mj, textRenderer._f10, INK)
            textRenderer._text_right(
                invoice, xs[3] + col_ws[3] - mm(2), y, base, textRenderer._f10, INK, span_tag=SpanTag.O
            )
            textRenderer._text_right(
                invoice, xs[4] + col_ws[4] - mm(2), y, vatp, textRenderer._f10, INK, span_tag=SpanTag.O
            )
            textRenderer._text_right(
                invoice, xs[5] + col_ws[5] - mm(2), y, vat, textRenderer._f10, INK, span_tag=SpanTag.O
            )
            textRenderer._text_right(invoice, xs[6] + col_ws[6] - mm(2), y, total, textRenderer._f10, INK)

            y += row_h
            hline(y, content_x0, content_x1, "thin")
            y += mm(2)

        y += mm(8)

        # =====================================================================
        # REKAPITULACE DPH
        # =====================================================================

        recap_w = content_w
        rx0 = content_x0
        rx1 = rx0 + recap_w
        ry0 = y
        vat_rows = max(2, len(getattr(data, "vat", [])))
        recap_h = mm(24) + mm(6) * vat_rows
        rect(rx0, ry0, rx1, ry0 + recap_h, "mid")

        textRenderer._text(invoice, (rx0 + mm(2), ry0 + mm(2)), "Rekapitulace DPH", textRenderer._f10b, INK)

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
                textRenderer._text(invoice, (cxs[0] + cws[0] - mm(20), header_y), c, textRenderer._f9, INK)
            else:
                textRenderer._text(invoice, (cxs[i] + cws[i] - mm(20), header_y), c, textRenderer._f9b, INK)

        row_y = header_y + mm(7)
        for v in getattr(data, "vat", [])[:3]:
            perc = safe(getattr(v, "vat_percentage", ""))
            base = fmt_money(getattr(v, "vat_base", 0))
            vatv = fmt_money(getattr(v, "vat", 0))
            tot = fmt_money(getattr(v, "total_with_vat", getattr(v, "price_with_vat", 0)))

            textRenderer._text(
                invoice, (cxs[0] + cws[0] - mm(20), row_y), f"{perc} %", textRenderer._f9, INK,
                span_tag=SpanTag.O
            )
            textRenderer._text(
                invoice, (cxs[1] + cws[1] - mm(20), row_y), base, textRenderer._f9, INK,
                span_tag=SpanTag.O
            )
            textRenderer._text(
                invoice, (cxs[2] + cws[2] - mm(20), row_y), vatv, textRenderer._f9, INK,
                span_tag=SpanTag.O
            )
            textRenderer._text(invoice, (cxs[3] + cws[3] - mm(20), row_y), tot, textRenderer._f9, INK)
            row_y += mm(6)

        y = ry0 + recap_h + mm(10)

        # =====================================================================
        # PODPISY + FOOTER
        # =====================================================================

        sig_y = _A4_H_PX - margin_b - mm(28)

        hline(sig_y + mm(18), content_x0, content_x0 + int(content_w * 0.40), "thin")
        hline(sig_y + mm(18), content_x0 + int(content_w * 0.55), content_x1, "thin")

        textRenderer._text(invoice, (content_x0, sig_y), "Fakturu převzal:", textRenderer._f10, INK)

        issuer = safe(getattr(data, "issuer", getattr(data, "handler", "")))
        textRenderer._text(invoice, (content_x0 + int(content_w * 0.45), sig_y), "Fakturoval:", textRenderer._f10, INK)
        textRenderer._text(invoice, (content_x0 + int(content_w * 0.57), sig_y), issuer, textRenderer._f10, INK)

        textRenderer._text_center(invoice, content_x0 + int(content_w * 0.20), sig_y + mm(20), "Zákazník", textRenderer._f10, INK)
        textRenderer._text_center(invoice, content_x0 + int(content_w * 0.78), sig_y + mm(20), safe(data.supplier.name), textRenderer._f10, INK)

        textRenderer._text_center(invoice, _A4_W_PX / 2, _A4_H_PX - margin_b - mm(8), "Strana 1 / 2", textRenderer._f9, INK)
        textRenderer._text_right(
            invoice,
            content_x1,
            _A4_H_PX - margin_b - mm(8),
            safe(getattr(data, "print_id", "ID tisku 1302710")),
            textRenderer._f9,
            INK,
        )

        invoice.image = img
        return True