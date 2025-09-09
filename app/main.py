from PIL import Image
import pytorch_lightning
from app.ie_engine.layoutlmv3.layout_invoice_dataset import layout_invoice_dataset
from app.ie_engine.layoutlmv3.layoutlmv3_pl_model import layoutlmv3_pl_model
from app.invoices_generator.core.enumerates.token_tags import token_tags
from app.invoices_generator.invoice_generator import invoice_generator

from PIL import Image

from transformers import AutoTokenizer, BertForPreTraining, LayoutLMv3Model, LayoutLMv3Processor
import torch
from app.ie_engine.enumerates.engines import engines
import pytesseract
import locale
from app.ie_engine.layoutlmv3.layout_trainer import layout_trainer

from pytesseract import Output
from torch.utils.data import DataLoader


def main()->None:
    
    

    inv_generator = invoice_generator()
    inv_generator.generate(15,3,3, engines.LAYOUTLMv3)

    #layout_trainer.train()

    # image = Image.open(r"app/data/validation/alza_invoice_2093-995205.png").convert("RGB")
    # layout_trainer.predict(image)


    #image = Image.open(r"app/data/validation/alza_invoice_2028-147018.png").convert("RGB")
    #trainer.predict(image)

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

    # model_name:str = "microsoft/layoutlmv3-base" 

    # max_length:int = 400
        
        
    # processor = LayoutLMv3Processor.from_pretrained(model_name,apply_ocr=False)
    # model:LayoutLMv3Model = LayoutLMv3Model.from_pretrained(model_name)

    # train_dataset = layout_invoice_dataset(data_root_folder_path="app/data/train", processor=processor)

    # test_dataset = layout_invoice_dataset(data_root_folder_path="app/data/test", processor=processor)

    # val_dataset = layout_invoice_dataset(data_root_folder_path="app/data/validation", processor=processor)

    # encoding = train_dataset[0]
    # encoding = encoding["encoding"]
    
    # print(encoding.keys())

    # for k,v in encoding.items():
    #     print(k, v.shape)

    # input_ids = encoding['input_ids'].long().unsqueeze(0)
    # bbox = encoding['bbox'].long().unsqueeze(0)
    # pixel_values = encoding['pixel_values'].float().unsqueeze(0)
    # attention_mask = encoding['attention_mask'].long().unsqueeze(0)

    # output = model(input_ids=input_ids,
    #                     bbox=bbox,
    #                     pixel_values=pixel_values,
    #                     attention_mask=attention_mask)  ## The output is [none, 709, 768], 
    #                                                                                                 # 512 tokens    

    

    # print(output)
    # print(output.last_hidden_state.shape)

if __name__=="__main__":
    main()