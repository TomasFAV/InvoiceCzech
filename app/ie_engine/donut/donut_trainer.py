import re
from PIL import Image
from typing import Any
import torch
from transformers import DonutProcessor, PreTrainedTokenizerFast, VisionEncoderDecoderModel, VisionEncoderDecoderConfig
from app.ie_engine.donut.donut_invoice_dataset import donut_invoice_dataset
from torch.utils.data import DataLoader
from app.ie_engine.donut.donut_module import donut_module, training_callback
import pytorch_lightning


class donut_trainer:

    def train()->tuple[Any, Any]:
        
        train_config = {"max_epochs":30,
            "val_check_interval":2, 
            "check_val_every_n_epoch":2,
            "gradient_clip_val":1.0,
            "num_training_samples_per_epoch": 800,
            "lr":3e-5,
            "train_batch_sizes": 1,
            "val_batch_sizes": 1,
            # "seed":2022,
            "num_nodes": 1,
            "warmup_steps": 300, # 800/8*30/10, 10%
            "result_path": "./result",
            "verbose": True,
            }

        model_name:str = "naver-clova-ix/donut-base-finetuned-cord-v2" 

        image_size:list[int] = [620, 877]
        max_length:int = 400
        
        config:VisionEncoderDecoderConfig = VisionEncoderDecoderConfig.from_pretrained(model_name)
        config.encoder.image_size = image_size

        config.decoder.max_length = max_length

        processor = DonutProcessor.from_pretrained(model_name)
        model:VisionEncoderDecoderModel = VisionEncoderDecoderModel.from_pretrained(model_name, config=config)

        train_dataset = donut_invoice_dataset(data_root_folder_path="app/data/train", processor=processor, model=model,max_length=max_length, task_start_token="<s_cord-v2>", prompt_end_token="<s_cord-v2>")

        test_dataset = donut_invoice_dataset(data_root_folder_path="app/data/test", processor=processor, model=model,max_length=max_length, task_start_token="<s_cord-v2>", prompt_end_token="<s_cord-v2>")

        val_dataset = donut_invoice_dataset(data_root_folder_path="app/data/validation", processor=processor, model=model,max_length=max_length, task_start_token="<s_cord-v2>", prompt_end_token="<s_cord-v2>")


        tokenizer: PreTrainedTokenizerFast = processor.tokenizer  # type: ignore[attr-defined]

        model.config.pad_token_id = tokenizer.pad_token_id
        model.config.decoder_start_token_id = int(tokenizer.convert_tokens_to_ids(['<s_cord-v2>'])[0])
        model.gradient_checkpointing_enable()

        train_dataloader:DataLoader = DataLoader(test_dataset, batch_size=train_config.get("train_batch_sizes"), shuffle=True, num_workers=4)
        #test_dataloader:DataLoader = DataLoader(test_dataset, batch_size=1, shuffle=True, num_workers=4)
        val_dataloader:DataLoader = DataLoader(val_dataset, batch_size=train_config.get("val_batch_sizes"), shuffle=False, num_workers=4)

        model_module = donut_module(train_config, processor, model)

        trainer = pytorch_lightning.Trainer(
            accelerator="gpu",
            devices=1,
            max_epochs=train_config.get("max_epochs"),
            val_check_interval=train_config.get("val_check_interval"),
            check_val_every_n_epoch=train_config.get("check_val_every_n_epoch"),
            gradient_clip_val=train_config.get("gradient_clip_val"),
            precision=16, # we'll use mixed precision
            num_sanity_val_steps=0,
            callbacks=[training_callback()],
        )

        lr_finder = trainer.tuner.lr_find(model_module)
        new_lr = lr_finder.suggestion()
        model_module.config["lr"] = new_lr

        trainer.fit(model_module, train_dataloaders=train_dataloader, val_dataloaders=val_dataloader)
    
    @staticmethod
    def predict(img:Image.Image) -> None:
        model_name: str = "TomasFAV/DonutInvoiceCzech"

        processor = DonutProcessor.from_pretrained(model_name)
        model: VisionEncoderDecoderModel = VisionEncoderDecoderModel.from_pretrained(model_name)
        device = "cuda" if torch.cuda.is_available() else "cpu"

        model.eval()
        model.to(device)

        # prepare encoder inputs
        pixel_values = processor(img, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device)
        # prepare decoder inputs
        task_prompt = "<s_cord-v2>"
        decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids
        decoder_input_ids = decoder_input_ids.to(device)
            
        # autoregressively generate sequence
        outputs = model.generate(
            pixel_values,
            decoder_input_ids=decoder_input_ids,
            max_length=model.decoder.config.max_position_embeddings,
            early_stopping=True,
            pad_token_id=processor.tokenizer.pad_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
            use_cache=True,
            num_beams=1,
            bad_words_ids=[[processor.tokenizer.unk_token_id]],
            return_dict_in_generate=True,
        )

        # turn into JSON
        seq = processor.batch_decode(outputs.sequences)[0]
        seq = seq.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
        seq = re.sub(r"<.*?>", "", seq, count=1).strip()  # remove first task start token
        print(seq)
        seq = processor.token2json(seq)
            
        print(seq)