from collections import defaultdict
from PIL import Image

from common.enumerates.SpanTag import SpanTag
from common.models.EndToEndModel import EndToEndModel
from invoices_generator.utility.invoice_consts import _A4_H_PX, _A4_W_PX
from common.enumerates.TokenTag import TokenTag

class DonutModel(EndToEndModel):

    def __init__(self, model_path="TomasFAV/DonutInvoiceCzechV0123"):
        super().__init__(model_path)

    def predict_labels(self, words:list[str])->list[TokenTag]:
        """
        Vrací pole dvojic id tagů, které je v pořadí slov, která byla zaslána k predikci
        """
        return [TokenTag.O for word in words]


    def predict_json(self, image:Image.Image) -> dict[str, str]:
        """
        Provede predikci nad OCR slovy a bounding boxy a vrátí JSON
        se složenými entitami pomocí stitching logiky přes overflow okna.
        """
        image = image.convert("RGB")
        image = image.resize((_A4_W_PX, _A4_H_PX))
        pixel_values = self._processor(image, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(self._device, dtype=self._model.dtype)
        #decoder_input_ids = processor.tokenizer("<s_cord-v2>", add_special_tokens=False, return_tensors="pt").input_ids.to(device)

        generated_ids = self._model.generate(
                    pixel_values,
                    max_length=768,
                    early_stopping=True,
                    pad_token_id=self._processor.tokenizer.pad_token_id,
                    eos_token_id=self._processor.tokenizer.eos_token_id,
                    use_cache=True,
                    bad_words_ids=[[self._processor.tokenizer.unk_token_id]],
                    #return_dict_in_generate=True,
                )

        generated_text = self._processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

        output_dict = defaultdict(str)
        for span_tag in SpanTag:
            if (span_tag != SpanTag.O):
                output_dict[span_tag.text] = ""


        for label, value in self.token2json(generated_text).items():
            if not isinstance(value, str):
                value = "" 
            output_dict[label] = value
    
        return output_dict