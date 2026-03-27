import json
import os
import sys

from tkinter import messagebox, filedialog, simpledialog
from typing import Any

import pytesseract

from requests import Session
from sympy import O, true
from invoices_generator.core.bank import bank
from invoices_generator.core.company import company
from shared.OperationResult import OperationResult
from invoice_annotator.utils.consts import DEFAULT_SEGMENT_COLOR, DEFAULT_SPAN_COLOR, DEFAULT_TOKEN_COLOR, SELECTED_SEGMENT_COLOR, SELECTED_SPAN_COLOR, SELECTED_TOKEN_COLOR, SET_SEGMENT_COLOR, SET_SPAN_COLOR, SET_TOKEN_COLOR
from invoice_annotator.utils.GSegment import GSegment
from invoices_generator.core.enumerates.segment_tags import segment_tags
from invoice_annotator.AI.LiltModel import LiltModel
from invoice_annotator.controller.Controller import Controller
from invoice_annotator.AppData import AppData
from invoice_annotator.enumerates.DataSource import DataSource
from invoice_annotator.utils.GRelationship import GRelationship
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
from invoice_annotator.utils.union_bbox import union_bbox
import tkinter.filedialog

from PIL import Image
from pytesseract import Output

from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import SPAN_TAGS_TO_IGNORE, span_tags
from invoices_generator.core.enumerates.token_tags import token_tags
from pathlib import Path


class ExportPageController(Controller):


    def __init__(self, session:Session):
        super().__init__(session)


    def export_invoice(self, export_directory_path:str, form_data:dict[str, Any],*args,**kwargs) -> OperationResult:
        if not self.session.image_path:
            return OperationResult(False)

        self.session.invoice.from_dict(form_data)

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
        class_names = "\n\t".join(f"{span_tag.code}: {span_tag.name}" for span_tag in span_tags if span_tag not in SPAN_TAGS_TO_IGNORE)
        yolo_yaml = f"""train: /content/data/train\nval: /content/data/validation\nnc: {len(span_tags) - len(SPAN_TAGS_TO_IGNORE)}\nname:\n\t{class_names}"""
        with open(os.path.join(export_dir, "yolo.yaml"),"w", encoding="utf-8") as f:
            f.write(yolo_yaml)


        result = OperationResult(True, self.session.image_path)
        self.session.reset()
        
        return result


    def export_layoutlmv3(self, export_img_name:str,  folder: str) -> bool:
        replaced = False #reprezentuje zda se již záznam v datech nacházel

        json_output: str = self.session.invoice.to_json_layoutlmv3()

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
        
        json_output: dict = self.session.invoice.to_json_donut(False, False)

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
        yolo_output: str = self.session.invoice.to_json_yolo()

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

        json_output: str = self.session.invoice.to_json_coco(export_json_path, export_img_name)

        #změn data
        with open(export_json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(json_output, ensure_ascii=False) + "\n")

        return True

    # -- Pomocné ---------------------------------------------------------------
