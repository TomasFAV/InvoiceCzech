import json
import os
from typing import Any
from requests import Session
from common.invoice.Processors.IEProcessors.DonutIEProcessor import DonutIEConfig
from common.invoice.Processors.IEProcessors.LayoutLMV3IEProcessor import LayoutLMV3IEConfig
from common.invoice.OperationResult import OperationResult
from common.controller.Controller import Controller
from PIL import Image

from common.enumerates.SpanTag import SPAN_TAGS_TO_IGNORE, SpanTag
from pathlib import Path


class ExportPageController(Controller):


    def __init__(self, session:Session):
        super().__init__(session)


    def export_invoice(self, export_directory_path:str, form_data:dict[str, Any],*args,**kwargs) -> OperationResult:
        if not self.session.image_path:
            return OperationResult(False)

        self.session.invoice_data.from_dict(form_data)

        export_img_name = Path(self.session.image_path).name
        export_dir = export_directory_path

        if(not self.export_layoutlmv3(export_img_name, export_directory_path)):
            return OperationResult(False)
        
        if(not self.export_donut(export_img_name, export_directory_path)):
            return OperationResult(False)
        
        if(not self.export_yolo(export_img_name, export_directory_path)):
            return OperationResult(False)
        
        if(not self.export_coco(export_img_name, export_directory_path)):
            return OperationResult(False)

        export_img_path = os.path.join(export_dir, "images" ,export_img_name)
        os.makedirs(os.path.join(export_dir, "images"), exist_ok=True)
        
        img = Image.open(self.session.image_path)
        img.save(export_img_path, format="PNG")


        # --- YOLO yaml cofing soubor ---
        class_names = "\n\t".join(f"{span_tag.code}: {span_tag.name}" for span_tag in SpanTag if span_tag not in SPAN_TAGS_TO_IGNORE)
        yolo_yaml = f"""train: /content/data/train\nval: /content/data/validation\nnc: {len(SpanTag) - len(SPAN_TAGS_TO_IGNORE)}\nname:\n\t{class_names}"""
        with open(os.path.join(export_dir, "yolo.yaml"),"w", encoding="utf-8") as f:
            f.write(yolo_yaml)


        result = OperationResult(True, self.session.image_path)
        self.session.reset()
        
        return result


    def export_layoutlmv3(self, export_img_name:str,  folder: str) -> bool:
        replaced = False #reprezentuje zda se již záznam v datech nacházel

        json_output: str = self._invoice_exporter.export_layoutlmv3(self.session.invoice, LayoutLMV3IEConfig.WITHOUT_TESSERACT)

        # vytvoření podsložky LayoutLMV3 (pokud neexistuje)
        export_dir = folder
        os.makedirs(export_dir, exist_ok=True)

        export_jsonl_path = os.path.join(export_dir, "metadata_layoutlmv3.jsonl")

        output = {
            "file_name": export_img_name,
            "data": json_output
        }

        lines = ""

        #načtu dosavadní hodnoty
        if Path(export_jsonl_path).exists():
            with open(export_jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    if(record["file_name"] == export_img_name):
                        lines += json.dumps(output, ensure_ascii=False, sort_keys=True) + "\n"
                        replaced = True
                    else:
                        lines += line   

        if not replaced:
            lines += json.dumps(output, ensure_ascii=False, sort_keys=True) + "\n"

        with open(export_jsonl_path, "w", encoding="utf-8") as f:
            f.write(lines)


        return True

    def export_donut(self,export_img_name:str, folder) -> bool:
        replaced = False #reprezentuje zda se již záznam v datech nacházel
        
        json_output: dict = self._invoice_exporter.export_donut(self.session.invoice, self.session.invoice_data, DonutIEConfig.FROM_INVOICE_DATA)

        # vytvoření podsložky LayoutLMV3 (pokud neexistuje)
        export_dir = folder
        os.makedirs(export_dir, exist_ok=True)

        export_jsonl_path = os.path.join(export_dir, "metadata_donut.jsonl")

        output = {
            "file_name": f"{export_img_name}",
            "ground_truth": {
                "gt_parse": json_output
            }
        }

        lines = ""

        #načtu dosavadní hodnoty
        if Path(export_jsonl_path).exists():
            with open(export_jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    if(record["file_name"] == export_img_name):
                        lines += json.dumps(output, ensure_ascii=False, sort_keys=True) + "\n"
                        replaced = True
                    else:
                        lines += line

        if not replaced:
            lines += json.dumps(output, ensure_ascii=False, sort_keys=True) + "\n"

        with open(export_jsonl_path, "w", encoding="utf-8") as f:
            f.write(lines)

        return True

    def export_yolo(self,export_img_name:str, folder) -> bool:
        yolo_output: str = self._invoice_exporter.export_yolo(self.session.invoice)

        # vytvoření podsložky LayoutLMV3 (pokud neexistuje)
        export_dir = os.path.join(folder, "labels")
        os.makedirs(export_dir, exist_ok=True)

        export_label_path = os.path.join(export_dir, export_img_name.replace(".png",".txt"))

        # přidej záznam do metadata.jsonl
        with open(export_label_path, "w", encoding="utf-8") as f:
            f.write(yolo_output)

        return True

    def export_coco(self,export_img_name:str, folder) -> bool:
        # vytvoření podsložky LayoutLMV3 (pokud neexistuje)
        export_dir = folder
        os.makedirs(export_dir, exist_ok=True)

        export_json_path = os.path.join(export_dir, "metadata_coco.json")

        json_output: str = self._invoice_exporter.export_coco(self.session.invoice, export_json_path, export_img_name)

        #změn data
        with open(export_json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(json_output, ensure_ascii=False) + "\n")

        return True

    # -- Pomocné ---------------------------------------------------------------
