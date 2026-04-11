
from copy import copy
from common.utils.GTesseract import GTesseract, TesseractConfig
from common.enumerates.SpanTag import SpanTag
from common.utils.utilities import get_dimensions_symetry, get_iou, merge_bboxes
from common.invoice.models.Invoice import Invoice


class InvoiceOCRAligner:

    def __init__(self):
        self.tesseract: GTesseract = GTesseract(TesseractConfig("ces"))

    def _find_best_tag_for_box(self, invoice:Invoice, bounding_box) -> tuple[int, float]:
        """
        Najde nejlepší anotovaný tag pro jeden OCR box.
        """
        best_tag = 0
        max_metric = 0.0

        for ann_token in invoice._tokens:
            overlap = get_iou(bounding_box, ann_token.b_box)
            relative_bbox_symetry = get_dimensions_symetry(bounding_box, ann_token.b_box)

            metric = overlap * relative_bbox_symetry

            if metric > max_metric:
                max_metric = metric
                best_tag = ann_token.tag.code

        return best_tag, max_metric


    def _map_tesseract_boxes_to_raw_tags(self, invoice:Invoice, tess_boxes: list, threshold: float = 0.05) -> list[int]:
        """
        Každému Tesseract boxu přiřadí nejlepší tag podle metriky:
        IoU * podobnost rozměrů.
        """
        raw_tags = []

        for t_box_px in tess_boxes:
            best_tag, max_metric = self._find_best_tag_for_box(invoice, t_box_px)

            if max_metric < threshold:
                best_tag = 0

            raw_tags.append(best_tag)

        return raw_tags

    def _flush_current_span(self, bounding_boxes:list[tuple[int,int,int,int]], current_span_token_ids:list[int], final_tags:list[int],
                            spans_boxes:list[tuple[int,int,int,int]],  spans_tags:list[int], spans_token_ids: list[int]) -> None:
            
            if not current_span_token_ids:
                return

            bboxes = [bounding_boxes[idx] for idx in current_span_token_ids]
            spans_boxes.append(merge_bboxes(bboxes))
            spans_tags.append(SpanTag.from__token_id(final_tags[-1]).code)
            spans_token_ids.append(copy(current_span_token_ids))


    def _bio_correction(self, raw_tags: list[int], bounding_boxes: list[tuple[int, int, int, int]],):
        spans_boxes: list = []
        spans_tags: list = []
        spans_token_ids: list = []
        current_span_token_ids: list[int] = []
        final_tags: list[int] = []

        last_base_tag: int | None = None

        for raw_tag in raw_tags:
            current_token_id = len(final_tags)

            if raw_tag == 0:
                self._flush_current_span(bounding_boxes, current_span_token_ids, final_tags, spans_boxes, spans_tags, spans_token_ids)
                current_span_token_ids = [current_token_id]
                final_tags.append(0)
                last_base_tag = None
                continue

            base_tag = raw_tag if raw_tag % 2 != 0 else raw_tag - 1

            if base_tag == last_base_tag:
                current_span_token_ids.append(current_token_id)
                final_tags.append(base_tag + 1)  # vynucené I-tag
                continue

            self._flush_current_span(bounding_boxes, current_span_token_ids, final_tags, spans_boxes, spans_tags, spans_token_ids)
            current_span_token_ids = [current_token_id]
            final_tags.append(base_tag)  # začátek nového B-tagu
            last_base_tag = base_tag

        self._flush_current_span(bounding_boxes, current_span_token_ids, final_tags, spans_boxes, spans_tags, spans_token_ids)

        return spans_token_ids, spans_boxes, spans_tags, final_tags
    
    
    def intersect_tokens_tesseract(self, invoice:Invoice):

        """
        Vezme data na faktuře a sjednotí s daty z ocr
        
        Výstupní boxy jsou v rozlišení fotky

        """

        # 1. Získání OCR dat z Tesseractu (v pixelech)
        tess_tokens, tess_boxes, tess_boxes_norm = self.tesseract.extract_text_from_image(invoice.image, 0)

        # 2. Mapování tagů pomocí IoU
        raw_tags = self._map_tesseract_boxes_to_raw_tags(invoice, tess_boxes)

        spans_token_ids, spans_boxes, spans_tags, final_tags = self._bio_correction(raw_tags, tess_boxes)
        
        return spans_token_ids, spans_boxes, spans_tags, tess_tokens, tess_boxes, final_tags
    