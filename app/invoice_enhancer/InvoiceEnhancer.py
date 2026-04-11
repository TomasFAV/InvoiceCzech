from datetime import datetime
import json
import math
import os
from pathlib import Path
import random
from typing import List


from common.invoice.processors.InvoiceImporter import InvoiceImporter
from common.invoice.renderers.InvoicePostProcessor import InvoicePostProcessor
from data_generator.DataGenerator import DataGenerator
from common.invoice.processors.IEProcessors.DonutIEProcessor import DonutIEConfig
from common.invoice.processors.IEProcessors.LayoutLMV3IEProcessor import LayoutLMV3IEConfig
from common.invoice.processors.InvoiceExporter import InvoiceExporter
from common.invoice.renderers.InvoiceRenderer import InvoiceRenderer
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.models.GSegment import GSegment
from common.invoice.models.GSpan import GSpan
from common.invoice.models.GToken import GToken
from common.enumerates.TokenTag import TokenTag
from common.enumerates.SegmentTag import SegmentTag
from common.enumerates.SpanTag import SpanTag

from common.data.invoice_consts import banks_, payments

from tqdm.auto import tqdm

class InvoiceEnhancer:
    """
                    STATICKÁ TŘÍDA
    Namnoží skutečné faktury pomocí syntetických údajů,
    které tam vloží na základě anotace daných faktur
    Vyžaduje složkovou strukturu:

    Složka:
        + images
        + labels
        - metadata_layoutlmv3.jsonl
        - ...
    


    """

    def enhance(layoutlmv3_path:str, instances_per_invoice=1)->None:
        #nactu nejdriv layoutlmv3
        #segmenty a spany
        invoice_renderer:InvoiceRenderer = InvoiceRenderer()
        invoice_post_processor:InvoicePostProcessor = InvoicePostProcessor()
        invoice_importer:InvoiceImporter = InvoiceImporter()
        invoice_exporter:InvoiceExporter = InvoiceExporter()

        layoutlmv3_path:Path = Path(layoutlmv3_path)
        if not layoutlmv3_path.exists():
            print("Soubor layoutlmv3 neexistuje")
            return
        


        parent_folder:Path = layoutlmv3_path.parent
        root_folder: Path = parent_folder.parent
        save_folder: Path = Path(os.path.join(root_folder, "enhanced_invoices"))
        images_path: Path = Path(os.path.join(save_folder, "images"))
        labels_path: Path = Path(os.path.join(save_folder, "labels"))

        os.makedirs(images_path, exist_ok=True)
        os.makedirs(labels_path, exist_ok=True)

        lines = ""

        with open(layoutlmv3_path, mode="r", encoding="utf-8") as file:
            lines = file.readlines()

        #jeden radek = jedna faktura
        for line in tqdm(lines):
            record = json.loads(line)

            for _ in range(instances_per_invoice):

                file_name = record["file_name"]

                tokens:List[GToken] = [GToken(None, token_text, token_box, TokenTag.from_id(token_tag_id)) for token_text, token_tag_id, token_box in zip(record["data"]["tokens"]["tokens"],
                                                                                                       record["data"]["tokens"]["tags"],
                                                                                                       record["data"]["tokens"]["boxes"])]
                
                #jelikož načítáme tokeny i spany po sobě, lze přímo vložit token_ids(v tomto případě indexy pole tokens)
                spans: List[GSpan] = [GSpan(None, box, SpanTag.from_id(tag_id), token_ids) for box, tag_id, token_ids in zip(record["data"]["spans"]["boxes"],
                                                                                      record["data"]["spans"]["tags"],
                                                                                      record["data"]["spans"]["token_ids"])]
                
                segments:List[GSegment] = [GSegment(None, box, SegmentTag.from_id(tag_id)) for box, tag_id in zip(record["data"]["segments"]["boxes"],
                                                                                                                   record["data"]["segments"]["tags"])]

            

                #nacteni obrazku
                img_path = Path(os.path.join(parent_folder,"images",file_name))
                if not img_path.exists():
                    continue

                items_quantity = InvoiceEnhancer.items_quantity(segments)
                items_quantity = max(2, items_quantity)

                invoice_data = DataGenerator.generate_invoice_data(items_quantity)

                invoice: Invoice = Invoice()

                invoice.load_image(img_path)

                invoice.load_tokens(tokens)
                invoice.load_spans(spans)
                invoice.load_segments(segments)

                invoice_renderer.enhance(invoice_data, invoice)
                invoice_post_processor.post_process(invoice)

                new_file_name = f"{file_name.replace(".png", "")}_enhanced_{"_".join(str(datetime.now()).split(" "))}.png"
                enhanced_img_path = Path(os.path.join(images_path, new_file_name)) 
                
                invoice.save_image(enhanced_img_path)

                #export faktury

                donut_metada_path = os.path.join(save_folder, "metadata_donut.jsonl")
                layoutlmv3_metada_path = os.path.join(save_folder, "metadata_layoutlmv3.jsonl")
                coco_metadata_path = os.path.join(save_folder, "metadata_coco.json")
                yolo_path = labels_path

                # --- 3. Zápis do DONUT (JSONL) ---
                donut_gt = {"gt_parse": invoice_exporter.export_donut(invoice, invoice_data, option=DonutIEConfig.FROM_INVOICE_DATA_WITH_CHECK)}
                donut_output = {
                    "file_name": new_file_name,
                    "ground_truth": donut_gt
                }
                with open(donut_metada_path, "a", encoding="utf-8") as f_donut:
                    f_donut.write(json.dumps(donut_output, ensure_ascii=False) + "\n")

                # --- 4. Zápis do LAYOUTLMv3 (JSONL) ---
                layout_data = invoice_exporter.export_layoutlmv3(invoice, option=LayoutLMV3IEConfig.WITH_TESSERACT)
                layout_output = {
                    "file_name": new_file_name,
                    "data": layout_data
                }
                with open(layoutlmv3_metada_path, "a",encoding="utf-8") as f_layout:
                    f_layout.write(json.dumps(layout_output, ensure_ascii=False) + "\n")

                # --- 5. Sběr dat pro COCO ---
                coco_data = invoice_exporter.export_coco(invoice, coco_metadata_path, new_file_name)
                with open(coco_metadata_path, "w", encoding="utf-8") as f_coco:
                    f_coco.write(json.dumps(coco_data, ensure_ascii=False, indent=4))
                    
                # --- 6. YOLO formát ---
                yolo_data = invoice_exporter.export_yolo(invoice)
                yolo_label_path = os.path.join(yolo_path, f"{new_file_name.replace(".png", ".txt")}") 
                with open(yolo_label_path, "w", encoding="utf-8") as f_yolo:
                    f_yolo.write(yolo_data)

    def items_quantity(segments:List[GSegment]):
        line_height = 50
        items_count = math.inf
        
        for segment in segments:
            if segment.tag == SegmentTag.ITEMS_BLOCK:
                items_count = min(items_count, (int)((segment.b_box[3] - segment.b_box[1])/line_height))
    
        if items_count == math.inf:
            return 0

        return items_count


