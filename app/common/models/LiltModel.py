from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import numpy as np

from common.enumerates.TokenTag import TokenTag
from common.models.TokenClassificationModel import TokenClassificationModel

class LiltModel(TokenClassificationModel):

    def __init__(self, model_path="TomasFAV/LiLTInvoiceCzechV0123"):
        super().__init__(model_path)

    def predict_labels(self, words:list[str], bboxes:list[tuple[int,int,int,int]])->list[TokenTag]:
        """
        Vrací pole dvojic id tagů, které je v pořadí slov, která byla zaslána k predikci
        """
        
        encoding = self._processor(
            words,
            boxes=bboxes,
            return_tensors="pt",
            return_overflowing_tokens=True, return_offsets_mapping =True,
            max_length=512,
            stride=128,
            padding="max_length",  
            truncation=True,        
            is_split_into_words=True,

        ).to(self._device)

        offset_mapping = encoding.pop('offset_mapping')

        encoding.pop('overflow_to_sample_mapping')

        for k,v in encoding.items():
            encoding[k] = v.to(self._device)

        outputs = self._model(**encoding)

        logits = outputs.logits
        predictions = logits.view(1, -1, logits.size(2)).squeeze(0).argmax(-1) #reshape na jeden dlouhy list predikci v 1D


        word_ids = []
        for batch_idx in range(len(encoding["input_ids"])):
            for id, word_id in enumerate(encoding.word_ids(batch_index=batch_idx)):
                word_ids.append(word_id) 

        is_subword = np.array(offset_mapping.view(1, -1, offset_mapping.size(2)).squeeze(0).tolist())[:,0] != 0


        true_words = [word_ids[idx] for idx, pred in enumerate(predictions) if not is_subword[idx]]
        true_predictions = [pred for idx, pred in enumerate(predictions) if not is_subword[idx]]

        labels = []
        already_done_words = set()

        for word, pred in zip(true_words, true_predictions):
            if word is None or word in already_done_words:
                continue

            tag:TokenTag =  TokenTag.from_id(pred.item())
            labels.append(tag)
            already_done_words.add(word)
        
        return labels


    def predict_json(self, words:list[str], bboxes:list[tuple[int,int,int,int]]) -> dict[str, str]:
        """
        Provede predikci nad OCR slovy a bounding boxy a vrátí JSON
        se složenými entitami pomocí stitching logiky přes overflow okna.
        """
        labels = self.predict_labels(words, bboxes)
        return self.labels_to_json(words, labels)