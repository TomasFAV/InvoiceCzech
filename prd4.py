import os
import random
from PIL import Image, ImageDraw, ImageFont

IMAGES_DIR = "./app/data/test/images/"
LABELS_DIR = "./app/data/test/labels/"   # <- sem dej txt labely
OUTPUT_DIR = "visualized_output/"

# id -> název (uprav dle sebe)
ID2LABEL = {
    0:"o", 1:"invoice_number", 2:"supp_register_id",
    3:"supp_tax_id", 4:"cust_register_id", 5:"cust_tax_id",
    6:"issue_date", 7:"taxable_supply_date", 8:"due_date",
    9:"payment_type", 10:"bank_account_number", 11:"iban",
    12:"bic", 13:"variable_symbol", 14:"const_symbol", 15:"total",
    16:"vat_percentage", 17:"vat_base", 18:"vat",
}

def get_color(tag_id: int):
    if tag_id == 0:
        return (220, 220, 220)
    random.seed(tag_id)
    return (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def yolo_line_to_xyxy_px(cls_id, xc, yc, bw, bh, img_w, img_h):
    """
    Převod YOLO (xc,yc,w,h) -> (x1,y1,x2,y2) v pixelech.
    Předpoklad: hodnoty jsou normalizované (0..1), ale toleruje i >1 (jen se ořízne).
    """
    xc_px = xc * img_w
    yc_px = yc * img_h
    bw_px = bw * img_w
    bh_px = bh * img_h

    x1 = xc_px - bw_px / 2
    y1 = yc_px - bh_px / 2
    x2 = xc_px + bw_px / 2
    y2 = yc_px + bh_px / 2

    x1 = clamp(x1, 0, img_w - 1)
    y1 = clamp(y1, 0, img_h - 1)
    x2 = clamp(x2, 0, img_w - 1)
    y2 = clamp(y2, 0, img_h - 1)

    return x1, y1, x2, y2

def read_yolo_txt(path):
    """
    Čte label soubor:
      class xc yc w h
    """
    boxes = []
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            parts = ln.split()
            if len(parts) < 5:
                continue
            cls = int(parts[0])
            xc, yc, bw, bh = map(float, parts[1:5])
            boxes.append((cls, xc, yc, bw, bh))
    return boxes

def visualize_one(img_path, label_path, out_path):
    img = Image.open(img_path).convert("RGBA")
    w, h = img.size

    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    for cls, xc, yc, bw, bh in read_yolo_txt(label_path):
        x1, y1, x2, y2 = yolo_line_to_xyxy_px(cls, xc, yc, bw, bh, w, h)
        color = get_color(cls)

        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        draw.rectangle([x1, y1, x2, y2], fill=(color[0], color[1], color[2], 50))

        label = ID2LABEL.get(cls, str(cls))
        draw.text((x1, max(0, y1 - 15)), label, fill=color, font=font)

    final_img = Image.alpha_composite(img, overlay).convert("RGB")
    final_img.save(out_path)

def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # projde všechny obrázky a hledá k nim .txt se stejným názvem
    for fn in os.listdir(IMAGES_DIR):
        if not fn.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            continue

        base = os.path.splitext(fn)[0]
        img_path = os.path.join(IMAGES_DIR, fn)
        label_path = os.path.join(LABELS_DIR, base + ".txt")

        if not os.path.exists(label_path):
            print(f"Chybí label: {label_path}")
            continue

        out_path = os.path.join(OUTPUT_DIR, "vis_" + fn)
        visualize_one(img_path, label_path, out_path)
        print(f"Hotovo: {out_path}")

if __name__ == "__main__":
    run()
