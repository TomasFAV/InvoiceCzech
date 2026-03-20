import json
import os
import random
from PIL import Image, ImageDraw, ImageFont

# --- KONFIGURACE ---
# V souboru prd.py změň:
JSON_PATH = "./app/data/test/metadata_coco.json" # Opraveno 'validation'
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

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        item = json.load(f)
        images = item["images"]
        annotations = item["annotations"]

        for image in images:
            file_name = image["file_name"]
            im = Image.open(os.path.join(IMAGES_DIR,file_name))
            im_draw = ImageDraw.Draw(im)

            for annotation in annotations:
                image_id = annotation["image_id"]
                bbox = annotation["bbox"]
                category:str = ID2LABEL[annotation["category_id"]]

                rect = (bbox[0], bbox[1], bbox[0]+bbox[2], bbox[1]+bbox[3])

                if(image_id == image["id"]):
                    im_draw.rectangle(rect   , outline=get_color(annotation["category_id"]), width=2)
                    im_draw.text((rect[0], rect[1]-10), text=category, fill=get_color(annotation["category_id"]))
            im.save(os.path.join(OUTPUT_DIR, file_name))           
            print(f"Vizualizace hotova: vis_{file_name}")

if __name__ == "__main__":
    run_visualization()
