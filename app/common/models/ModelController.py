from collections import defaultdict
from enum import Enum
from typing import Any
from common.models.DonutModel import DonutModel
from common.models.TokenClassificationModel import TokenClassificationModel
from common.enumerates.TokenTag import TokenTag
from common.models.BertModel import BertModel
from common.models.LayoutLMV3Model import LayoutLMV3Model
from common.models.LiltModel import LiltModel
from PIL import Image

class Model(Enum):
    Bert = "Bert"
    LiLT = "LiLT"
    LayoutLMV3 = "LayoutLMV3"
    Donut = "Donut"


class ModelController:

    def __init__(self):
        self.__bert_model: BertModel = BertModel()
        self.__lilt_model: LiltModel = LiltModel()
        self.__layoutlmv3_model: LayoutLMV3Model = LayoutLMV3Model()
        self.__donut_model: DonutModel = DonutModel()
    

    def predict_labels(self, image:Image.Image, words:list[str], bboxes:list[tuple[int,int,int,int]], option:Model)->list[TokenTag]:
        if option == Model.Bert:
            return self.__bert_model.predict_labels(words)
        elif option == Model.LiLT:
            return self.__lilt_model.predict_labels(words, bboxes)
        elif option == Model.LayoutLMV3:
            return self.__layoutlmv3_model.predict_labels(image, words, bboxes)
        elif option == Model.Donut:
            return self.__donut_model.predict_labels(words)
        elif option == Model.Pix2Struct:
            ...

    def predict_json(self, image:Image.Image, words:list[str], bboxes:list[tuple[int,int,int,int]], option:Model) -> dict[str, str]:
        """
        Provede predikci nad OCR slovy a bounding boxy a vrátí JSON
        se složenými entitami pomocí stitching logiky přes overflow okna.
        """
        if option == Model.Bert:
            return self.__bert_model.predict_json(words)
        elif option == Model.LiLT:
            return self.__lilt_model.predict_json(words, bboxes)
        elif option == Model.LayoutLMV3:
            return self.__layoutlmv3_model.predict_json(image, words, bboxes)
        elif option == Model.Donut:
            return self.__donut_model.predict_json(image)
        elif option == Model.Pix2Struct:
            ...

    def labels_to_json(self, words, labels) -> dict[str, str]:
        return self.__bert_model.labels_to_json(words, labels)