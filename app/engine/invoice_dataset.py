import json
from PIL import Image
from typing import Any, List, Tuple, Dict, Union
import torch
from torch.utils.data import Dataset
import os
from transformers import PreTrainedTokenizerFast, VisionEncoderDecoderModel
from transformers import DonutProcessor

added_tokens:list[Any] = []

class invoice_dataset(Dataset[Tuple[torch.Tensor, torch.Tensor, str]]):


    def __init__(self, data_root_folder_path:str, processor:DonutProcessor, model:VisionEncoderDecoderModel, max_length: int,
                 task_start_token: str = "<s>",prompt_end_token: str|None = None):
        
        super().__init__()

        self.data_root_folder_path:str = data_root_folder_path
        self.processor:DonutProcessor = processor
        self.max_length:int = max_length
        self.model = model
        self.task_start_token = task_start_token
        self.prompt_end_token = prompt_end_token if prompt_end_token else task_start_token

        metadata_path = data_root_folder_path + "/metadata.jsonl"

        lines:list[str]
        data:List[dict[str, Any]] = list()

        new_tokens: set[str] = set()

        with open(metadata_path, mode="r", encoding="utf-8") as f:
            for line in f:
                output:Dict[str, Any] = json.loads(line)

                tokens:str = self.json2token(output['ground_truth']['gt_parse'], new_tokens) #do new_tokens se sbírají nově nalezené tokeny 
                output['ground_truth']['gt_parse'] = tokens
                data.append(output)


        #přidám až všechny najednou
        if new_tokens:
            self.add_tokens(list(new_tokens))

        self.add_tokens([self.task_start_token, self.prompt_end_token])

        self.data:List[Dict[str, Any]] = data




    def json2token(self, obj:Union[Dict[str, Any], List[Any], str, int, float, None],  new_tokens: set[str], update_special_tokens_for_json_key: bool = True, sort_json_key: bool = True)->str:
        """
        REKURZIVNĚ Převede json string na formát tokenů a nové tokeny přidá do tokenizátoru
        """
        if isinstance(obj, dict):
            if len(obj) == 1:
                return str(next(iter(obj.values())))
            
            output = ""
            keys = sorted(obj.keys(), reverse=True) if sort_json_key else obj.keys()
            for k in keys:
                if update_special_tokens_for_json_key:
                    new_tokens.update([fr"<s_{k}>", fr"</s_{k}>"])
                    #self.add_tokens([fr"<s_{k}>", fr"</s_{k}>"])
                output += (
                    fr"<s_{k}>"
                    + self.json2token(obj[k], new_tokens, update_special_tokens_for_json_key, sort_json_key)
                    + fr"</s_{k}>"
                )
            return output
        
        elif isinstance(obj, list):
            return "<sep/>".join([self.json2token(item,new_tokens, update_special_tokens_for_json_key, sort_json_key) for item in obj])
        else:
            obj_str = str(obj)
            if f"<{obj_str}/>" in added_tokens:
                obj_str = f"<{obj_str}/>"  # pro kategorické speciální tokeny
            return obj_str

    def add_tokens(self, list_of_tokens: List[str])->None:
        """
        Přidá token do tokenizeru a zvětší embeding dekodéru
        """
        tokenizer: PreTrainedTokenizerFast = self.processor.tokenizer # type: ignore[attr-defined]

        newly_added_num:int = tokenizer.add_tokens(list_of_tokens)
        if newly_added_num > 0:
            self.model.decoder.resize_token_embeddings(len(tokenizer))
            added_tokens.extend(list_of_tokens)

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index:int)-> Tuple[torch.Tensor, torch.Tensor, str]:
        
        image_path:str = self.data_root_folder_path + "/" +self.data[index]["file_name"]
        image = Image.open(image_path).convert("RGB")
        
        target_sequence:str  = self.data[index]["ground_truth"]["gt_parse"]

        #embeding tokenizovaného jsonu + předzpracování obrázku
        encoding = self.processor(
            images=image,
            text=target_sequence,
            return_tensors="pt",
            max_length=self.max_length,
            padding="max_length",
            truncation=True
        )

        return encoding.pixel_values.squeeze(0), encoding.labels.squeeze(0), target_sequence