import json
from pathlib import Path
from typing import Any
from common.enumerates.SpanTag import SPAN_TAGS_TO_IGNORE, SpanTag
from common.utils.consts import _A4_H_PX, _A4_W_PX
from common.invoice.models.Invoice import Invoice
from common.invoice.OperationResult import OperationResult
from common.invoice.processors.IEProcessors.IEProcessor import IEProcessor

class CocoIEProcessor(IEProcessor):


    def _export(self, invoice:Invoice, path_to_metadata_coco:str, invoice_file_path:str)->dict[str, Any]:
        result: OperationResult = OperationResult(False)

        result = self.__to_json_coco(invoice, path_to_metadata_coco, invoice_file_path)

        if(not result.ok):
            if isinstance(result.passed_value, str):
                raise result.passed_value
            else:
                raise "Something went wrong, CocoExport"
            
        return result.passed_value

    def _import(self)->bool:
        """Není implementováno"""

        raise "Not Implemented"
    
    def __to_json_coco(self, invoice:Invoice, path_to_metadata_coco:str, invoice_file_path:str)->OperationResult:
        """
        path_to_metadata...cesta k metadata_coco.json, kvůli načtení dosavadních hodnot
        img_name...jméno obrázku pod kterým bude uložen...obrazek123456789.png
        vrátí dosavadní data obohacená o data této faktury
        """
        if not Path(path_to_metadata_coco).exists():
            with open(path_to_metadata_coco, mode="w") as f:
                f.write(json.dumps({
                "images":[],
                "annotations":[],
                "categories":[]
            }))

        with open(path_to_metadata_coco, "r") as f:
            try:
                data = json.load(f)
            except:
                data = {"images":[], "annotations":[], "categories":[]}

            images = data.get("images", list())
            annotations = data.get("annotations", list())


            #filtrace spanů na základě bbox zda je na stránce a také tagu
            filtered = []
            w_img, h_img = _A4_W_PX, _A4_H_PX

            for span in invoice._spans:
                if(span.tag.code == 0 or span.tag in SPAN_TAGS_TO_IGNORE 
                
                or span.b_box[0] > w_img or span.b_box[2] > w_img 
                or span.b_box[0] < 0 or span.b_box[2] < 0

                or span.b_box[1] > h_img or span.b_box[3] > h_img
                or span.b_box[1] < 0 or span.b_box[3] < 0):
                
                    continue
                
                filtered.append((span.tokens, span.b_box, span.tag.code))  

            max_image_id = 0
            image_to_delete = None
            
            for image in images:
                if(image["file_name"] == invoice_file_path):
                    image_to_delete = image
                max_image_id = max(max_image_id, image["id"])

            

            if image_to_delete:
                annotations = [anno for anno in annotations if anno["image_id"] != image_to_delete["id"]]    
                images.remove(image_to_delete)
            

            _, spans_boxes, spans_tag_list = map(list, zip(*filtered)) if filtered else ([], [], [])
            
            for i, (box, tag) in enumerate(zip(spans_boxes, spans_tag_list)):
                # COCO vyžaduje [x_min, y_min, width, height] v pixelech
                x1, y1, x2, y2 = box
                width = x2 - x1
                height = y2 - y1 

                max_anno_id = 0 

                for anno in annotations:
                    max_anno_id = max(max_anno_id, anno["id"])
                
                ann = {
                    "id": max_anno_id+1,
                    "image_id": max_image_id+1,
                    "category_id": tag,
                    "bbox": [float(x1), float(y1), float(width), float(height)],
                    "area": float(width * height),
                    "iscrowd": 0,
                    "segmentation": [], # Pro detekci boxů stačí prázdné
                }
                annotations.append(ann)


            
            images.append({
                        "id": max_image_id+1,
                        "file_name": invoice_file_path,
                        "height": _A4_H_PX,
                        "width": _A4_W_PX,
                    })
            
            categories = [{"id": item.code, "name": item.text, "supercategory": None} for item in SpanTag]

            output = {
                "images":images,
                "annotations":annotations,
                "categories":categories
            }

            return OperationResult(True, output)