from abc import ABC, abstractmethod
from collections import defaultdict
import re

import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer, AutoProcessor, VisionEncoderDecoderConfig, VisionEncoderDecoderModel
from common.utils.utilities import normalize_text


class EndToEndModel(ABC):

    def __init__(self, model_path=""):
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        
        config = VisionEncoderDecoderConfig.from_pretrained(model_path)
        config.dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        self._model = VisionEncoderDecoderModel.from_pretrained(model_path, config=config).to(self._device)
        self._processor = AutoProcessor.from_pretrained(model_path, use_fast=True)    

    def token2json(self, tokens, is_inner_value=False):
        output = {}
        # Matches <s_tag>content</s_tag>
        pattern = r"<s_(?P<key>[^>]+)>(?P<value>.*?)<\s*/\s*s_(?P=key)>"

        matches = list(re.finditer(pattern, tokens, re.DOTALL | re.IGNORECASE))

        if not matches:
            # If no tags, treat as leaf node or raw text
            return tokens.strip()

        for match in matches:
            key = match.group("key")
            value_str = match.group("value").strip()

            # Recursive step for nested tags
            if "<s_" in value_str:
                value = self.token2json(value_str, is_inner_value=True)
            else:
                # Handle list splitting by <sep/>
                parts = [v.strip() for v in value_str.split("<sep/>") if v.strip()]
                value = parts[0] if len(parts) == 1 else parts

            # Grouping logic for repeating keys
            if key in output:
                if isinstance(output[key], list):
                    output[key].append(value)
                else:
                    output[key] = [output[key], value]
            else:
                output[key] = value

        return output if output else tokens

    @abstractmethod
    def predict_json(self)->dict[str, str]:
        ...