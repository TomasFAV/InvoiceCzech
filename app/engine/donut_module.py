import re
from typing import Any, List, Mapping, Tuple
from nltk import edit_distance # type: ignore[import]
import numpy as np
from torch.utils.data import DataLoader

import torch

import pytorch_lightning
from transformers import DonutProcessor,PreTrainedTokenizerFast, VisionEncoderDecoderModel, VisionEncoderDecoderConfig
from PIL import Image

class donut_module(pytorch_lightning.LightningModule):
    
    def __init__(self, train_config:dict[Any], processor:DonutProcessor, model:VisionEncoderDecoderModel, max_length:int = 768)->None:
        super().__init__()
        self.config:dict[Any] = train_config
        self.processor:DonutProcessor = processor
        self.model:VisionEncoderDecoderModel = model
        self.max_length = max_length

    def forward(self, pixel_values: torch.Tensor) -> Any:
        return self.model(pixel_values)

    def training_step(self, batch:List[Tuple[torch.Tensor, torch.Tensor, str]], batch_idx:int)->Any:
        pixel_values, labels, _ = batch
        
        outputs = self.model(pixel_values, labels=labels)
        loss = outputs.loss
        self.log("train_loss", loss)
        return loss

    def configure_optimizers(self)->Any:
        return torch.optim.AdamW(self.parameters(), lr=self.config.get("lr"))

    def validation_step(self, batch:Tuple[torch.Tensor, torch.Tensor, str], batch_idx:int)->List[Any]:
        pixel_values, _, answers = batch
        batch_size = pixel_values.shape[0]
        # prompt do modelu...startovací token
        decoder_input_ids = torch.full((batch_size, 1), fill_value=self.model.config.decoder_start_token_id, device=self.device)
        
        outputs = self.model.generate(pixel_values,
                                   decoder_input_ids=decoder_input_ids,
                                   max_length=self.max_length,
                                   early_stopping=True,
                                   pad_token_id=self.processor.tokenizer.pad_token_id,
                                   eos_token_id=self.processor.tokenizer.eos_token_id,
                                   use_cache=True,
                                   num_beams=1,
                                   bad_words_ids=[[self.processor.tokenizer.unk_token_id]],
                                   return_dict_in_generate=True,)
    
        predictions = []
        for seq in self.processor.tokenizer.batch_decode(outputs.sequences):
            seq = seq.replace(self.processor.tokenizer.eos_token, "").replace(self.processor.tokenizer.pad_token, "")
            seq = re.sub(r"<.*?>", "", seq, count=1).strip()
            predictions.append(seq)

        scores = []
        for pred, answer in zip(predictions, answers):
            pred = re.sub(r"(?:(?<=>) | (?=</s_))", "", pred)

            answer = answer.replace(self.processor.tokenizer.eos_token, "")
            scores.append(edit_distance(pred, answer) / max(len(pred), len(answer)))

            print(f"Prediction: {pred}")
            print(f"    Answer: {answer}")
            print(f"Prdicted JSON: {self.processor.token2json(pred)}")
            print(f" Normed ED: {scores[0]}")

        self.log("val_edit_distance", np.mean(scores))
        
        return scores
    

class training_callback(pytorch_lightning.Callback):
    def __init__(self, save_path="app/engine/models"):
        super().__init__()
        self.save_path = save_path

    def on_train_epoch_end(self, trainer, pl_module):
        print(f"Saving model after epoch {trainer.current_epoch}")
        pl_module.model.save_pretrained(f"{self.save_path}/epoch_{trainer.current_epoch}")
        pl_module.processor.save_pretrained(f"{self.save_path}/epoch_{trainer.current_epoch}")

    def on_train_end(self, trainer, pl_module):
        print("Saving final model after training")
        pl_module.model.save_pretrained(f"{self.save_path}/final")
        pl_module.processor.save_pretrained(f"{self.save_path}/final")
        
