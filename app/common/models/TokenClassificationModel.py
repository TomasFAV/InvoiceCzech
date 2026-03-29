from abc import ABC, abstractmethod
from collections import defaultdict

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer, AutoProcessor
from common.enumerates.SpanTag import SpanTag
from common.utils.utilities import normalize_text


class TokenClassificationModel(ABC):

    def __init__(self, model_path=""):
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self._model = AutoModelForTokenClassification.from_pretrained(model_path).to(self._device)
        self._processor = AutoProcessor.from_pretrained(model_path, apply_ocr=False)    

    def __insert_curent_span_into_dict(self, current_label:str, current_span_words: list[str], dictionary: dict[str, str]):
        key = normalize_text(current_label)
        if key == "payment_type":
            dictionary[key] = " ".join(current_span_words).strip()
        else:
            dictionary[key] = "".join(current_span_words).strip()

    def labels_to_json(self, words, labels):
        pred_dict:dict[str, str] = defaultdict(str)
        for span_tag in SpanTag:
            if (span_tag != SpanTag.O):
                pred_dict[span_tag.text] = ""

        current_entity_words = []
        current_label = None

        for word, label in zip(words, labels):
            label = label.text

            if label.startswith("b_"):
                    if current_label and current_entity_words:
                        self.__insert_curent_span_into_dict(current_label, current_entity_words, pred_dict)
                    current_label = label[2:]
                    current_entity_words = [word]
            elif label.startswith("i_") and current_label == label[2:]:
                current_entity_words.append(word)
            else:
                if current_label and current_entity_words:
                    self.__insert_curent_span_into_dict(current_label, current_entity_words, pred_dict)
                current_label = None
                current_entity_words = []

        if current_label and current_entity_words:
            self.__insert_curent_span_into_dict(current_label, current_entity_words, pred_dict)

        return pred_dict
    

    @abstractmethod
    def predict_json(self)->dict[str, str]:
        ...