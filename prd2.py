import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

# --- KONFIGURACE ---
# V souboru prd.py změň:
JSONL_PATH = "./app/data/test/metadata_layoutlmv3.jsonl" # Opraveno 'validation'
# A ujisti se, že obrázky jsou taky správně:
IMAGES_DIR = "./app/data/test/images/"          # Složka s obrázky
OUTPUT_DIR = "visualized_output/"      # Kam se uloží vykreslené obrázky

# Tvůj maping ID -> Název (uprav podle svého Enumu)
# Pokud máš ID v JSONL jako čísla, tento slovník je převede na čitelný text
tags_list = [
    (0,"o"), (1,"invoice_number"), (2,"supp_register_id"), 
    (3,"supp_tax_id"), (4,"cust_register_id"), (5,"cust_tax_id"),
    (6,"issue_date"), (7,"taxable_supply_date"), (8,"due_date"),
    (9,"payment_type"), (10,"bank_account_number"), (11,"iban"),
    (12,"bic"), (13,"variable_symbol"), (14,"const_symbol"), (15,"total"),
    (16,"vat_percentage"), (17,"vat_base"), (18,"vat"), 
]

# Inline vytvoření id2label
ID2LABEL = {id: label for id, label, *rest in tags_list}

# --- POMOCNÉ FUNKCE ---

def get_color(tag_id):
    """Vytvoří unikátní barvu pro každou entitu (B a I mají stejnou barvu)."""
    if tag_id == 0:
        return (220, 220, 220) # Světle šedá pro pozadí (O)
    
    # Entita B (lichá) a I (sudá) dostanou stejný seed pro barvu
    base_id = tag_id if tag_id % 2 != 0 else tag_id - 1
    random.seed(base_id)
    return (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))

def run_visualization():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            file_name = item["file_name"]
            
            # Pozor: u tebe jsou data v item["data"]["tokens"]
            tokens_data = item["data"]["spans"]
            img_path = os.path.join(IMAGES_DIR, file_name)

            if not os.path.exists(img_path):
                print(f"Obrázek {file_name} nenalezen v {IMAGES_DIR}")
                continue

            img = Image.open(img_path).convert("RGBA")
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(overlay)
            w, h = img.size

            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()

            for token, box, tag_id in zip(tokens_data["token_ids"], tokens_data["boxes"], tokens_data["tags"]):
                # De-normalizace (box je v 0-1000)
                x1, y1, x2, y2 = (
                    box[0] * w / 1000,
                    box[1] * h / 1000,
                    box[2] * w / 1000,
                    box[3] * h / 1000
                )
                
                x1, y1, x2, y2 = box[0], box[1], box[2], box[3]

                color = get_color(tag_id)
                
                # Kreslíme obdélník
                draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
                
                
                # Výplň pro důležité tagy
                draw.rectangle([x1, y1, x2, y2], fill=(color[0], color[1], color[2], 50))
                # Textový štítek
                label = ID2LABEL.get(tag_id, str(tag_id))
                draw.text((x1, y1 - 15), label, fill=color, font=font)

            # Sloučení vrstev a uložení
            final_img = Image.alpha_composite(img, overlay).convert("RGB")
            final_img.save(os.path.join(OUTPUT_DIR, "vis_" + file_name))
            print(f"Vizualizace hotova: vis_{file_name}")

if __name__ == "__main__":
    run_visualization()
