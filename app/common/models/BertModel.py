from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import numpy as np

from common.enumerates.TokenTag import TokenTag
from common.models.TokenClassificationModel import TokenClassificationModel

class BertModel(TokenClassificationModel):

    def __init__(self, model_path="TomasFAV/BertInvoiceCzechV0123"):
        super().__init__(model_path)    
       

    def predict_labels(self, words: list[str]) -> list[TokenTag]:
        """
        Vrací pole tagů ve stejném pořadí jako vstupní slova.
        Každému slovu přiřadí první predikci z jeho prvního výskytu
        napříč všemi overflow okny.
        """

        encoding = self._processor(
            words,
            return_tensors="pt",
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            max_length=512,
            stride=128,
            padding="max_length",
            truncation=True,
            is_split_into_words=True,
        ).to(self._device)

        # offset_mapping si necháme bokem, model ho nepotřebuje
        offset_mapping = encoding.pop("offset_mapping")
        encoding.pop("overflow_to_sample_mapping", None)

        outputs = self._model(**encoding)
        all_predictions = outputs.logits.argmax(-1)  # [num_windows, seq_len]

        labels: list[TokenTag | None] = [None] * len(words)

        for window_idx in range(all_predictions.shape[0]):
            predictions_tensor = all_predictions[window_idx]
            word_ids = encoding.word_ids(batch_index=window_idx)
            offsets = offset_mapping[window_idx]

            last_word_idx = None

            for token_idx, pred_id in enumerate(predictions_tensor):
                curr_word_idx = word_ids[token_idx]

                # přeskoč speciální tokeny
                if curr_word_idx is None:
                    continue

                # přeskoč další subtokeny stejného slova
                if curr_word_idx == last_word_idx:
                    continue

                # pojistka: ber jen první subtoken slova
                if offsets[token_idx][0].item() != 0:
                    continue

                # pokud už jsme slovo vyřešili v předchozím okně, nech ho být
                if labels[curr_word_idx] is not None:
                    last_word_idx = curr_word_idx
                    continue

                labels[curr_word_idx] = TokenTag.from_id(pred_id.item())
                last_word_idx = curr_word_idx

        # fallback, kdyby nějaké slovo nebylo pokryto
        return [
            label if label is not None else TokenTag.from_id(0)
            for label in labels
        ]


    def predict_json(self, words:list[str]) -> dict[str, str]:
        """
        Provede predikci nad OCR slovy a bounding boxy a vrátí JSON
        se složenými entitami pomocí stitching logiky přes overflow okna.
        """
        labels = self.predict_labels(words)
        return self.labels_to_json(words, labels)