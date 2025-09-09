from collections import defaultdict
import json
from PIL import Image
from typing import Any, List, Tuple, Dict
import torch
from torch.utils.data import Dataset
from transformers import BatchEncoding, LayoutLMv3Processor
from unidecode import unidecode

class layout_invoice_dataset(Dataset[Tuple[torch.Tensor, torch.Tensor, str]]):


    def __init__(self, data_root_folder_path:str, processor:LayoutLMv3Processor):
        
        super().__init__()

        self.data_root_folder_path:str = data_root_folder_path
        self.processor:LayoutLMv3Processor = processor
    

        metadata_path = data_root_folder_path + "/metadata.jsonl"
        data:List[dict[str, Any]] = list()

        with open(metadata_path, mode="r", encoding="utf-8") as f:
            for line in f:
                output:Dict[str, Any] = json.loads(line)
                data.append(output)

        self.data:List[Dict[str, Any]] = data


    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index:int)-> BatchEncoding:
        
        image_path:str = self.data_root_folder_path + "/" +self.data[index]["file_name"]
        image = Image.open(image_path).convert("RGB")

        words = self.data[index]["data"]["tokens"]["tokens"]
        boxes = self.data[index]["data"]["tokens"]["boxes"]
        word_labels = self.data[index]["data"]["tokens"]["tags"]
        spans = self.data[index]["data"]["spans"]
        relationships = self.data[index]["data"]["relationships"]

        #normalizace slov(NUTNÉ!!!!)...v opačném případě rozděluje slova s diakritikou na více slov a potom nesedí word_labels
        words = [unidecode(word) for word in words]
        
        encoding = self.processor(image, words, boxes=boxes, word_labels=word_labels, truncation=True, stride = 128, 
        padding="max_length", max_length=512, return_overflowing_tokens=True, return_offsets_mapping=True, return_tensors="pt")
        #word_ids encodingu mají pro každý input_id index prvku z words ke kterému patří

        encoding.pop('offset_mapping')

        encoding.pop('overflow_to_sample_mapping')

        windows = encoding["input_ids"].shape[0]
        
        input_ids      = encoding["input_ids"].tolist()          # [T_text]
        
        #pole dvojic (start_index, end_index) [exkluzivní] pro každé encodované slovo do pole input_ids 
        words_subtokens_map = [[(-1,-1) for x in range(len(input_ids[b]))] for b in range(len(input_ids))] #zarovnáno na [b,512] 

        for b in range(len(input_ids)):
            word_ids = encoding.word_ids(batch_index=b)
            gl_index = 0
            for (index,word_id) in enumerate(word_ids):
                if(word_id is None):
                    continue
                if(words_subtokens_map[b][word_id][0] == -1):
                    words_subtokens_map[b][word_id]= (index, index)
                    continue
                words_subtokens_map[b][word_id] = (words_subtokens_map[b][word_id][0], index)


        pv = encoding.get("pixel_values", None)
        pv = torch.stack(pv, dim=0)             # [C,H,W] -> [1,C,H,W]
        encoding["pixel_values"] = pv

        encoding = pad_to_two_windows(
            encoding,
            pad_token_id=self.processor.tokenizer.pad_token_id,
            ignore_index=-100
        )

        return dict(encodings=encoding, words = words, word_input_ids_mapping = words_subtokens_map,
                    spans=spans, relationships=relationships, windows=windows)
    
def pad_to_two_windows(enc, pad_token_id: int, ignore_index: int = -100):
    """
    Pokud má BatchEncoding tvar [1, 512, ...], doplní prázdné druhé okno tak,
    aby vše mělo [2, 512, ...]. Pokud už má [2, 512, ...], vrátí beze změny.
    Pokud by bylo víc než 2, vyhodí chybu.
    """
    s = enc["input_ids"].shape[0]
    if s == 2:
        return enc
    if s > 2:
        raise ValueError(f"max 2 okna, přišlo {s}.")

    # ========== s == 1 → vytvoř prázdné druhé okno ==========
    pad_rows = {}

    # Sekvenční pole [s, 512]
    for key in ("input_ids", "attention_mask", "token_type_ids"):
        if key in enc:
            row = enc[key][0].clone()
            if key == "input_ids":
                row[:] = pad_token_id           # samé PADy
            else:
                row.zero_()                      # masky/typy na nulu
            pad_rows[key] = row.unsqueeze(0)

    # BBox [s, 512, 4]
    if "bbox" in enc:
        row = enc["bbox"][0].clone()
        row.zero_()
        pad_rows["bbox"] = row.unsqueeze(0)

    # Labels (NER) [s, 512] – ignorovat v lossu
    for key in ("labels", "word_labels"):
        if key in enc:
            row = torch.full(enc[key].shape, ignore_index)
            pad_rows[key] = row

    # Offset mapping [s, 512, 2] – volitelně vynulovat
    if "offset_mapping" in enc:
        row = enc["offset_mapping"][0].clone()
        row.zero_()
        pad_rows["offset_mapping"] = row.unsqueeze(0)

    # Overflow map [s] – nové okno mapuj na stejný sample (typicky 0)
    if "overflow_to_sample_mapping" in enc:
        row = enc["overflow_to_sample_mapping"][0:1].clone()
        pad_rows["overflow_to_sample_mapping"] = row

    # pixel_values [s, C, H, W] – duplikuj první (tvar musí sedět)
    if "pixel_values" in enc:
        row = enc["pixel_values"][0:1] 
        row = row.clone()
        pad_rows["pixel_values"] = row

    # Zřetězit po první dimenzi
    for key, pad_row in pad_rows.items():
        enc[key] = torch.cat([enc[key], pad_row], dim=0)

    return enc

def collate_joint(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    #Rozbalení a nstakování tenzorů fixní délky z encodingu
    enc_keys = batch[0]["encodings"].keys()
    out = {k: torch.stack([b["encodings"][k] for b in batch], dim=0) for k in enc_keys}

    #Proměnně dlouhé věci jako listy (žádný stack)
    out["words"] = [b["words"] for b in batch]
    out["word_input_ids_mapping"] = [b["word_input_ids_mapping"] for b in batch]
    out["spans"] = [b["spans"] for b in batch]
    out["relationships"] = [b["relationships"] for b in batch]
    out["windows"] = [b["windows"] for b in batch]
    return out
