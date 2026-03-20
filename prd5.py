import json
import os
import random
from PIL import Image, ImageDraw, ImageFont


# --- KONFIGURACE ---
# V souboru prd.py změň:
JSON_PATH = "./app/data/test/metadata_layoutlmv3.jsonl" # Opraveno 'validation'
# A ujisti se, že obrázky jsou taky správně:
IMAGES_DIR = "./app/data/test/images/"          # Složka s obrázky
OUTPUT_DIR = "visualized_output/"      # Kam se uloží vykreslené obrázky

# Tvůj maping ID -> Název (uprav podle svého Enumu)
# Pokud máš ID v JSONL jako čísla, tento slovník je převede na čitelný text
tags_list = [
    (0,"o"),
    (1,"supp_block"),(2,"cust_block"),
    (3,"items_block"), (4, "vat_block")]

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
        for line in f:
            record = json.loads(line)
            
            bboxes = record["data"]["segments"]["boxes"]
            tag_ids = record["data"]["segments"]["tags"]
            
            file_name = record["file_name"]
            
            im = Image.open(os.path.join(IMAGES_DIR,file_name))
            im_draw = ImageDraw.Draw(im)

            for box, tag_id in zip(bboxes, tag_ids):
                category:str = ID2LABEL[tag_id]

                rect = (box[0], box[1], box[2], box[3])

                im_draw.rectangle(rect   , outline=get_color(tag_id), width=2)
                im_draw.text((rect[0], rect[1]-10), text=category, fill=get_color(tag_id))
                
            im.save(os.path.join(OUTPUT_DIR, file_name))           
            print(f"Vizualizace hotova: vis_{file_name}")

if __name__ == "__main__":
    run_visualization()
