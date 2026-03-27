from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch
import numpy as np

class LiltModel:

    def __init__(self, model_path="TomasFAV/LiLTInvoiceCzechV0123"):
        
        self.__device = "cuda" if torch.cuda.is_available() else "cpu"

        self.__model = AutoModelForTokenClassification.from_pretrained(model_path).to(self.__device)
        self.__tokenizer = AutoTokenizer.from_pretrained(model_path)

    def predict(self, words, bboxes):
        """
        Vrací pole dvojic id tagů, které je v pořadí slov, která byla zaslána k predikci
        """
        
        encoding = self.__tokenizer(
            words,
            boxes=bboxes,
            return_tensors="pt",
            return_overflowing_tokens=True, return_offsets_mapping =True,
            max_length=512,
            stride=128,
            padding="max_length",  
            truncation=True,        
            is_split_into_words=True,

        )

        offset_mapping = encoding.pop('offset_mapping')

        encoding.pop('overflow_to_sample_mapping')

        for k,v in encoding.items():
            encoding[k] = v.to(self.__device)

        outputs = self.__model(**encoding)

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
            labels.append(pred.item())
            already_done_words.add(word)
        
        return labels