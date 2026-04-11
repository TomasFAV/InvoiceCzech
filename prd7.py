import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

# =========================
# KONFIGURACE
# =========================
JSONL_PATH = "./app/data/test/metadata_layoutlmv3.jsonl"
IMAGES_DIR = "./app/data/test/images/"
OUTPUT_DIR = "visualized_output"

DRAW_SEGMENTS = False
DRAW_TOKENS = True

# Prefix výstupního souboru
OUTPUT_PREFIX = "vis_"

# =========================
# MAPOVÁNÍ LABELŮ
# =========================

# Segment-level labely
segment_tags_list = [
    (0,"o"),
    (1,"supp_block"),
    (2, "supp_inner_block"),
    (3,"cust_block"),
    (4,"cust_inner_block"),
    (5,"items_block"),
    (6, "vat_block")    
]
SEGMENT_ID2LABEL = {tag_id: label for tag_id, label in segment_tags_list}

# Token-level labely
TOKEN_ID2LABEL = {
    0: "O",

    1: "B_INVOICE_NUMBER",
    2: "I_INVOICE_NUMBER",

    3: "B_SUPPLIER_REGISTER_ID",
    4: "I_SUPPLIER_REGISTER_ID",

    5: "B_SUPPLIER_TAX_ID",
    6: "I_SUPPLIER_TAX_ID",

    7: "B_CUSTOMER_REGISTER_ID",
    8: "I_CUSTOMER_REGISTER_ID",

    9: "B_CUSTOMER_TAX_ID",
    10: "I_CUSTOMER_TAX_ID",

    11: "B_ISSUE_DATE",
    12: "I_ISSUE_DATE",

    13: "B_TAXABLE_SUPPLY_DATE",
    14: "I_TAXABLE_SUPPLY_DATE",

    15: "B_DUE_DATE",
    16: "I_DUE_DATE",

    17: "B_PAYMENT_TYPE",
    18: "I_PAYMENT_TYPE",

    19: "B_BANK_ACCOUNT_NUMBER",
    20: "I_BANK_ACCOUNT_NUMBER",

    21: "B_IBAN",
    22: "I_IBAN",

    23: "B_BIC",
    24: "I_BIC",

    25: "B_VARIABLE_SYMBOL",
    26: "I_VARIABLE_SYMBOL",

    27: "B_CONST_SYMBOL",
    28: "I_CONST_SYMBOL",

    29: "B_TOTAL",
    30: "I_TOTAL",
}


# =========================
# POMOCNÉ FUNKCE
# =========================

def get_color(tag_id: int):
    """
    Vrátí stabilní barvu pro daný tag.
    U BIO tagů mají B/I stejnou barvu.
    """
    if tag_id == 0:
        return (180, 180, 180)

    # Pro tokenové BIO labely: B/I stejné barvy
    base_id = tag_id if tag_id % 2 != 0 else tag_id - 1
    random.seed(base_id)
    return (
        random.randint(30, 200),
        random.randint(30, 200),
        random.randint(30, 200),
    )


def ensure_output_dir(path: str):
    os.makedirs(path, exist_ok=True)


def load_font(size=30):
    font_paths = [
        "/home/tom-k/Desktop/Zpracovani_faktur/fonts/ARIAL.ttf"
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "arial.ttf",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue

    return ImageFont.load_default()


def draw_label_background(draw, x, y, text, font, fill_color, text_color=(255, 0, 0, 255)):
    """
    Nakreslí text s podkladovým obdélníkem, aby byl dobře čitelný.
    """
    try:
        bbox = draw.textbbox((x, y), text, font=font)
        tx1, ty1, tx2, ty2 = bbox
    except Exception:
        text_w, text_h = draw.textsize(text, font=font)
        tx1, ty1, tx2, ty2 = x, y, x + text_w, y + text_h

    pad = 2
    #draw.rectangle(
    #    [tx1 - pad, ty1 - pad, tx2 + pad, ty2 + pad],
    #    fill=fill_color
    #)
    draw.text((x, y), text, fill=text_color, font=font)


def normalize_box_if_needed(box, img_w, img_h):
    """
    Pokud jsou bboxy normalizované na 0-1000, převede je na pixely.
    Pokud už vypadají jako pixely, vrátí je beze změny.
    """
    x1, y1, x2, y2 = box

    # Heuristika:
    # když všechny souřadnice jsou <= 1000, může jít o LayoutLM normalizaci.
    # Ale protože některé malé obrázky můžou mít taky pixely < 1000,
    # necháme možnost jednoduché detekce:
    if max(box) <= 1000 and (img_w > 1000 or img_h > 1000):
        return (
            x1,
            y1,
            x2,
            y2,
        )

    return x1, y1, x2, y2


def clamp_box(box, img_w, img_h):
    x1, y1, x2, y2 = box
    x1 = max(0, min(img_w - 1, x1))
    y1 = max(0, min(img_h - 1, y1))
    x2 = max(0, min(img_w - 1, x2))
    y2 = max(0, min(img_h - 1, y2))
    return x1, y1, x2, y2


def draw_tokens(draw, tokens_data, img_w, img_h, font):
    """
    Tokeny: tenčí obrys + jemná průhledná výplň + label.
    """
    tokens = tokens_data.get("tokens", [])
    boxes = tokens_data.get("boxes", [])
    tags = tokens_data.get("tags", [])

    for token, box, tag_id in zip(tokens, boxes, tags):
        x1, y1, x2, y2 = normalize_box_if_needed(box, img_w, img_h)
        x1, y1, x2, y2 = clamp_box((x1, y1, x2, y2), img_w, img_h)

        color = get_color(tag_id)
        if tag_id == 0:
            continue
        # Jemná výplň
        if tag_id != 0:
            draw.rectangle([x1, y1, x2, y2], fill=(color[0], color[1], color[2], 45))

        # Obrys
        draw.rectangle([x1, y1, x2, y2], outline=(color[0], color[1], color[2], 180), width=1)

        # Label jen pro nenulové tagy
        if tag_id != 0:
            label = TOKEN_ID2LABEL.get(tag_id, str(tag_id))
            label_y = max(0, y1 - 21)
            draw_label_background(
                draw=draw,
                x=x1,
                y=label_y,
                text=label,
                font=font,
                fill_color=(color[0], color[1], color[2], 255),
                text_color=(255,0,0,255)
            )


def draw_segments(draw, segments_data, img_w, img_h, font):
    """
    Segmenty: výraznější obrys + label.
    """
    boxes = segments_data.get("boxes", [])
    tags = segments_data.get("tags", [])

    for box, tag_id in zip(boxes, tags):
        x1, y1, x2, y2 = normalize_box_if_needed(box, img_w, img_h)
        x1, y1, x2, y2 = clamp_box((x1, y1, x2, y2), img_w, img_h)

        color = get_color(tag_id)
        label = SEGMENT_ID2LABEL.get(tag_id, str(tag_id))

        # Výraznější obrys segmentu
        draw.rectangle([x1, y1, x2, y2], outline=(color[0], color[1], color[2], 255), width=3)

        # Popisek segmentu
        label_y = max(0, y1 - 18)
        draw_label_background(
            draw=draw,
            x=x1,
            y=label_y,
            text=f"SEG: {label}",
            font=font,
            fill_color=(color[0], color[1], color[2], 255),
            text_color=(0,0,255,255)
        )


# =========================
# HLAVNÍ LOGIKA
# =========================

def run_visualization():
    ensure_output_dir(OUTPUT_DIR)
    font = load_font(15)

    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[Řádek {line_idx}] Neplatný JSON: {e}")
                continue

            file_name = item.get("file_name")
            if not file_name:
                print(f"[Řádek {line_idx}] Chybí 'file_name'")
                continue

            img_path = os.path.join(IMAGES_DIR, file_name)
            if not os.path.exists(img_path):
                print(f"Obrázek {file_name} nenalezen v {IMAGES_DIR}")
                continue

            try:
                img = Image.open(img_path).convert("RGBA")
            except Exception as e:
                print(f"Nelze otevřít obrázek {img_path}: {e}")
                continue

            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            img_w, img_h = img.size

            data = item.get("data", {})

            # 1) nejdřív tokeny
            if DRAW_TOKENS and "tokens" in data:
                draw_tokens(draw, data["tokens"], img_w, img_h, font)

            # 2) potom segmenty, aby byly nahoře a dobře vidět
            if DRAW_SEGMENTS and "segments" in data:
                draw_segments(draw, data["segments"], img_w, img_h, font)

            final_img = Image.alpha_composite(img, overlay).convert("RGB")

            output_name = OUTPUT_PREFIX + file_name
            output_path = os.path.join(OUTPUT_DIR, output_name)
            final_img.save(output_path)

            print(f"Vizualizace hotova: {output_path}")


if __name__ == "__main__":
    run_visualization()