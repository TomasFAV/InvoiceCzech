import re
from PIL import Image
import torch
from transformers import DonutProcessor, PreTrainedTokenizerFast, VisionEncoderDecoderModel, VisionEncoderDecoderConfig
from app.engine.invoice_dataset import invoice_dataset
from torch.utils.data import DataLoader
from app.engine.donut_module import donut_module, training_callback
import pytorch_lightning

from app.engine.trainer import trainer
from app.invoices.invoice_generator import invoice_generator

from PIL import Image

from transformers import AutoTokenizer, BertForPreTraining
import torch

import pytesseract

def main()->None:
    
    #inv_generator = invoice_generator()
    #inv_generator.generate(6000,0,0)

    #trainer.train()

    image = Image.open(r"app/data/validation/alza_invoice_1989-293324.png").convert("RGB")
    trainer.predict(image)

    # lang = 'ces'

    # # If you don't have tesseract executable in your PATH, include the following:
    # pytesseract.pytesseract.tesseract_cmd = r'E:\user\plocha\BP\packages\tesseract.exe'
    # # Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'
    # # Simple image to string
    # print(pytesseract.image_to_string(Image.open('app/data/test/alza_invoice_2082-272234.png'), lang=lang))
    # print("===============================================================================================")


    # # Get verbose data including boxes, confidences, line and page numbers
    # print(pytesseract.image_to_data(Image.open('app/data/test/alza_invoice_2082-272234.png'), lang=lang))
    # print("===============================================================================================")

    # input("Hotovo, Enter pro ukončení…")
    
if __name__=="__main__":
    main()