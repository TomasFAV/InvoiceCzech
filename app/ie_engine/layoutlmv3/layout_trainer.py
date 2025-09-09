import re
from PIL import Image
from typing import Any
import pytesseract
import torch
from transformers import LayoutLMv3Config, LayoutLMv3Processor,  LayoutLMv3Model
from app.ie_engine.donut.donut_module import training_callback
import pytorch_lightning

from app.ie_engine.layoutlmv3.layout_invoice_dataset import collate_joint, layout_invoice_dataset
from app.ie_engine.layoutlmv3.layoutlmv3_pl_model import layoutlmv3_pl_model
from app.invoices_generator.core.enumerates.relationship_types import relationship_types
from app.invoices_generator.core.enumerates.token_tags import token_tags
from torch.utils.data import DataLoader

from pytesseract import Output

class layout_trainer:

    def train()->tuple[Any, Any]:
        
        model_name:str = "microsoft/layoutlmv3-base"         
        
        processor = LayoutLMv3Processor.from_pretrained(model_name,apply_ocr=False)
        model:LayoutLMv3Model = LayoutLMv3Model.from_pretrained(model_name)

        train_dataset = layout_invoice_dataset(data_root_folder_path="app/data/train", processor=processor)

        test_dataset = layout_invoice_dataset(data_root_folder_path="app/data/test", processor=processor)

        val_dataset = layout_invoice_dataset(data_root_folder_path="app/data/validation", processor=processor)

        # encoding = train_dataset[0]["encoding"]
        # print(encoding.keys())

        # for k,v in encoding.items():
        #     print(k, v.shape)

        train_dataloader:DataLoader = DataLoader(train_dataset, batch_size=4, shuffle=False, num_workers=4, collate_fn=collate_joint)
        val_dataloader:DataLoader = DataLoader(test_dataset, batch_size=1, shuffle=False, num_workers=4, collate_fn=collate_joint)

        module = layoutlmv3_pl_model(len(token_tags), len(relationship_types), model)

        #print(encoding['input_ids'])
        #print(processor.tokenizer.decode(encoding['input_ids']))

        trainer = pytorch_lightning.Trainer(
            accelerator="gpu",
            devices=1,
            max_epochs=10,
            check_val_every_n_epoch=2,
            precision=16,
            num_sanity_val_steps=0,
            callbacks=[],
        )

        # lr_finder = trainer.tuner.lr_find(module)
        # new_lr = lr_finder.suggestion()
        # module.lr = new_lr

        trainer.fit(module, train_dataloaders=train_dataloader, val_dataloaders=val_dataloader)

    def predict(img: Image)->Any:
        model_name:str = "microsoft/layoutlmv3-base" 
        
        
        processor = LayoutLMv3Processor.from_pretrained(model_name,apply_ocr=False)
        model:LayoutLMv3Model = LayoutLMv3Model.from_pretrained(model_name)

        lang = 'ces'

        # If you don't have tesseract executable in your PATH, include the following:
        pytesseract.pytesseract.tesseract_cmd = r'E:\user\plocha\BP\packages\tesseract.exe'
        # Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'
        # Simple image to string
        
        width, height = img.size

        data = pytesseract.image_to_data(img, lang=lang, output_type=Output.DICT)
        
        bbox = [(l/width*1000,t/height*1000,(l+w)/width*1000,(t+h)/height*1000)  for l,t,w,h,c in zip(data["left"], data["top"], data["width"], data["height"], data["conf"]) if c != -1 and c > 40]
        text = [t  for t,c in zip(data["text"], data["conf"]) if c != -1 and c > 40]
        
        bbox = bbox[:130] #130 tokenů je maximum
        text = text[:130]

        encoding = processor(img, text, boxes=bbox, return_tensors="pt")

        module = layoutlmv3_pl_model(len(token_tags), model)

        outputs =  module(encoding)

        predictions = outputs['logits'].argmax(-1)
        true_predictions, _ = module.get_labels(predictions)
        print(true_predictions)