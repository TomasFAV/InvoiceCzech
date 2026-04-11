from collections import defaultdict
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import numpy as np

from PIL import Image

from common.utils.consts import _A4_H_PX, _A4_W_PX
from common.enumerates.TokenTag import TokenTag
from common.models.TokenClassificationModel import TokenClassificationModel

class LayoutLMV3Model(TokenClassificationModel):

    def __init__(self, model_path="TomasFAV/Layoutlmv3InvoiceCzechV0123"):
        super().__init__(model_path)

    def predict_labels(
    self,
    image: Image.Image,
    words: list[str],
    bboxes: list[tuple[int, int, int, int]]
    ) -> list[TokenTag]:
        """
        Vrací tagy ve stejném pořadí jako vstupní words.
        """
        if len(words) != len(bboxes):
            raise ValueError(f"words ({len(words)}) a bboxes ({len(bboxes)}) nemají stejnou délku")

        image = image.convert("RGB")
        image = image.resize((_A4_W_PX, _A4_H_PX))

        encoding = self._processor(
            image,
            text=words,
            boxes=bboxes,
            return_tensors="pt",
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            max_length=512,
            stride=128,
            padding="max_length",
            truncation=True,
        )

        offset_mapping = encoding.pop("offset_mapping")
        encoding.pop("overflow_to_sample_mapping", None)

        # Jen pokud by pixel_values nebyly tensor:
        # if isinstance(encoding["pixel_values"], list):
        #     encoding["pixel_values"] = torch.stack(encoding["pixel_values"])

        inputs = {}
        for k, v in encoding.items():
            if isinstance(v, list):
                # typicky pixel_values u LayoutLMv3
                v = torch.stack(v)
            inputs[k] = v.to(self._device)

        with torch.no_grad():
            outputs = self._model(**inputs)

        all_predictions = outputs.logits.argmax(-1).cpu()
        offset_mapping = offset_mapping.cpu()

        labels: list[TokenTag | None] = [None] * len(words)

        for window_idx in range(all_predictions.shape[0]):
            predictions_tensor = all_predictions[window_idx]
            word_ids = encoding.word_ids(batch_index=window_idx)
            offsets = offset_mapping[window_idx]

            for token_idx, pred_id in enumerate(predictions_tensor):
                word_id = word_ids[token_idx]

                if word_id is None:
                    continue

                # ber jen první subtoken slova
                if offsets[token_idx][0].item() != 0:
                    continue

                # už vyřešeno v předchozím nebo tomto okně
                if labels[word_id] is not None:
                    continue

                labels[word_id] = TokenTag.from_id(pred_id.item())

        return [
            label if label is not None else TokenTag.from_id(0)
            for label in labels
        ]


    def predict_json(self, image:Image.Image, words:list[str], bboxes:list[tuple[int,int,int,int]]) -> dict[str, str]:
        """
        Provede predikci nad OCR slovy a bounding boxy a vrátí JSON
        se složenými entitami pomocí stitching logiky přes overflow okna.
        """
        labels = self.predict_labels(image, words, bboxes)
        return self.labels_to_json(words, labels)