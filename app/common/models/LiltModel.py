from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import numpy as np

from common.enumerates.TokenTag import TokenTag
from common.models.TokenClassificationModel import TokenClassificationModel

class LiltModel(TokenClassificationModel):

    def __init__(self, model_path="TomasFAV/LiLTInvoiceCzechV0123"):
        super().__init__(model_path)

    def predict_labels(self, words: list[str], bboxes: list[tuple[int,int,int,int]]) -> list[TokenTag]:
        encoding = self._processor(
            words,
            boxes=bboxes,
            return_tensors="pt",
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            max_length=512,
            stride=128,
            padding="max_length",
            truncation=True,
            is_split_into_words=True,
        )

        offset_mapping = encoding.pop("offset_mapping")
        encoding.pop("overflow_to_sample_mapping", None)

        for k in encoding:
            encoding[k] = encoding[k].to(self._device)

        with torch.no_grad():
            outputs = self._model(**encoding)

        logits = outputs.logits.argmax(-1).cpu()   # [batch, seq_len]
        offset_mapping = offset_mapping.cpu()

        labels: list[TokenTag | None] = [None] * len(words)

        for batch_idx in range(logits.size(0)):
            word_ids = encoding.word_ids(batch_index=batch_idx)

            for token_idx, word_id in enumerate(word_ids):
                if word_id is None:
                    continue

                start_offset = offset_mapping[batch_idx, token_idx, 0].item()
                if start_offset != 0:
                    continue  # subword -> nechci

                if labels[word_id] is None:
                    pred_id = logits[batch_idx, token_idx].item()
                    labels[word_id] = TokenTag.from_id(pred_id)

        return [label if label is not None else TokenTag.O for label in labels]


    def predict_json(self, words:list[str], bboxes:list[tuple[int,int,int,int]]) -> dict[str, str]:
        """
        Provede predikci nad OCR slovy a bounding boxy a vrátí JSON
        se složenými entitami pomocí stitching logiky přes overflow okna.
        """
        labels = self.predict_labels(words, bboxes)
        return self.labels_to_json(words, labels)