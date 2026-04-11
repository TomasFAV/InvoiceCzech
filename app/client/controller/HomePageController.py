import json
import os
from typing import Any
from transformers import AutoTokenizer
from common.Session import Session
from common.models.ModelController import Model, ModelController
from common.models.LiltModel import LiltModel
from common.utils.GTesseract import GTesseract, TesseractConfig
from common.enumerates.TokenTag import TokenTag
from common.invoice.models.GToken import GToken
from common.utils.consts import DEFAULT_TOKEN_COLOR, SET_TOKEN_COLOR
from common.invoice.processors.IEProcessors.DonutIEProcessor import DonutIEConfig
from common.invoice.processors.IEProcessors.LayoutLMV3IEProcessor import LayoutLMV3IEConfig
from common.invoice.OperationResult import OperationResult
from common.controller.Controller import Controller
from PIL import Image

from common.enumerates.SpanTag import SPAN_TAGS_TO_IGNORE, SpanTag
from pathlib import Path


class HomePageController(Controller):


    def __init__(self, session:Session):
        super().__init__(session)
        self.pytesseract: GTesseract = GTesseract(TesseractConfig("ces"))
        self.ai_model_controller: ModelController = ModelController()

    def open_invoice(self, file_path:str, *kwargs) -> OperationResult:

        if not Path(file_path).exists():
            return

        self.session.reset()
        self.session.invoice.load_image(Path(file_path))

        self.load_invoice(file_path)

        return OperationResult(True, file_path)

    def load_invoice(self, file_path:Path|str)->bool:
        #podivam se do rodice, jestli nema soubor metadata_layoutlmv3.jsonl
        file_path = Path(file_path)
        parent_path = file_path.parent.parent.absolute()

        layoutlmv3_path = Path(os.path.join(parent_path, "metadata_layoutlmv3.jsonl"))
        if not layoutlmv3_path.exists():
            return False
        
        
        layout_result:bool = self.invoice_from_layoutlmv3(self.session.invoice, layoutlmv3_path, file_path)

        donut_path = Path(os.path.join(parent_path, "metadata_donut.jsonl"))
        if not donut_path.exists():
            return False

        donut_result:bool =  self.invoice_data_from_donut(self.session.invoice_data, donut_path, file_path)

        return layout_result and donut_result #buď se podařilo načíst obojí => True, jinak False

    def extract_invoice_data_from_image(self, model:Model) -> dict[str, str]:
        image = self.get_invoice_image()
        self.session.invoice.clear()

        text, bbox, bbox_norm = self.pytesseract.extract_text_from_image(image)

        if model is not Model.Donut:

            labels = self.ai_model_controller.predict_labels(self.session.invoice.image, text, bbox_norm, model)
            json = self.ai_model_controller.labels_to_json(text, labels)

            self.session.invoice.clear()

            for i, label in enumerate(labels):
                if label == TokenTag.O:
                    continue

                color = DEFAULT_TOKEN_COLOR if label == TokenTag.O else SET_TOKEN_COLOR 
                self.append_token(GToken(None, text[i], bbox[i], label, color))
        
        else:
            self.session.invoice.clear()
            json = self.ai_model_controller.predict_json(self.session.invoice.image, text, bbox_norm, model)

        return json

    def export_invoice(self, export_directory_path:str, form_data:dict[str, Any],*args,**kwargs) -> OperationResult:
        if not self.session.image_path:
            return OperationResult(False)

        self.session.invoice_data.from_dict(form_data)

        export_img_name = Path(self.session.image_path).name
        export_dir = export_directory_path

        if(not self.export_json(export_img_name, export_directory_path)):
            return OperationResult(False)

        result = OperationResult(True, self.session.image_path)
        self.session.reset()
        
        return result

    # -- Pomocné ---------------------------------------------------------------

    def export_json(self,export_img_name:str, folder) -> bool:
        replaced = False #reprezentuje zda se již záznam v datech nacházel
        
        json_output: dict = self._invoice_exporter.export_donut(self.session.invoice, self.session.invoice_data, DonutIEConfig.FROM_INVOICE_DATA)

        # vytvoření podsložky LayoutLMV3 (pokud neexistuje)
        export_dir = folder
        os.makedirs(export_dir, exist_ok=True)

        export_jsonl_path = os.path.join(export_dir, f"{export_img_name}.json")

        output = json_output

        with open(export_jsonl_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(output, ensure_ascii=False, sort_keys=True))

        return True