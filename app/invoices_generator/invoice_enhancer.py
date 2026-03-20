from datetime import datetime
import json
import math
import os
from pathlib import Path
import random
from tkinter import font
from turtle import width
from typing import Any

from sympy import root


from invoices_generator.templates.components.bodies.table_a import table_a
from invoices_generator.templates.components.bodies.table_b import table_b
from invoices_generator.templates.components.vats.vat_c import vat_c
from invoices_generator.templates.components.vats.vat_b import vat_b
from invoices_generator.templates.components.vats.vat_a import vat_a
from invoice_annotator.utils.GSegment import GSegment
from invoice_annotator.utils.GSpan import GSpan
from invoice_annotator.utils.GToken import GToken
from invoices_generator.core.enumerates.token_tags import token_tags
from invoices_generator.core.invoice_component import invoice_component
from invoices_generator.templates.components.suppliers_customers.company_a import company_a
from invoices_generator.templates.components.suppliers_customers.company_b import company_b
from invoices_generator.templates.components.suppliers_customers.company_c import company_c
from invoices_generator.utility.utils import fit_line_bounding_box_font, fit_text_bounding_box_font, fmt_money, text_height, text_width
from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.company import company
from invoices_generator.core.enumerates.segment_tags import segment_tags
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.DInvoice import DInvoice
from invoices_generator.core.invoice_item import invoice_item
from invoices_generator.invoice_generator import invoice_generator
from invoices_generator.core.span import span
from invoices_generator.core.segment import segment
from invoices_generator.utility.invoice_consts import *
from invoices_generator.core.bank import bank

from PIL import Image
from PIL.ImageDraw import ImageDraw, Draw
from PIL.ImageFont import truetype, FreeTypeFont

from tqdm.auto import tqdm

class invoice_enhancer:
    """
                    STATICKÁ TŘÍDA
    Namnoží skutečné faktury pomocí syntetických údajů,
    které tam vloží na základě anotace daných faktur
    Vyžaduje složkovou strukturu:

    Složka:
        + images
        + labels
        - metadata_layoutlmv3.jsonl
        - ...
    


    """

    def __init__(self):
        ...

    def enhance(layoutlmv3_path:str, instances_per_invoice=1)->None:
        #nactu nejdriv layoutlmv3
        #segmenty a spany
        layoutlmv3_path:Path = Path(layoutlmv3_path)
        if not layoutlmv3_path.exists():
            print("Soubor layoutlmv3 neexistuje")
        


        parent_folder:Path = layoutlmv3_path.parent
        root_folder: Path = parent_folder.parent
        save_folder: Path = Path(os.path.join(root_folder, "enhanced_invoices"))
        images_path: Path = Path(os.path.join(save_folder, "images"))
        labels_path: Path = Path(os.path.join(save_folder, "labels"))

        os.makedirs(images_path, exist_ok=True)
        os.makedirs(labels_path, exist_ok=True)

        lines = ""

        with open(layoutlmv3_path, mode="r", encoding="utf-8") as file:
            lines = file.readlines()

        #jeden radek = jedna faktura
        for line in tqdm(lines):
            record = json.loads(line)

            for _ in range(instances_per_invoice):

                file_name = record["file_name"]

                if file_name == "4bdcd86b-1.png":
                    print("Hi")

                tokens:List[GToken] = [GToken(None, token_text, token_box, token_tags.from_id(token_tag_id)) for token_text, token_tag_id, token_box in zip(record["data"]["tokens"]["tokens"],
                                                                                                       record["data"]["tokens"]["tags"],
                                                                                                       record["data"]["tokens"]["boxes"])]
                
                #jelikož načítáme tokeny i spany po sobě, lze přímo vložit token_ids(v tomto případě indexy pole tokens)
                spans: List[GSpan] = [GSpan(None, box, span_tags.from_id(tag_id), token_ids) for box, tag_id, token_ids in zip(record["data"]["spans"]["boxes"],
                                                                                      record["data"]["spans"]["tags"],
                                                                                      record["data"]["spans"]["token_ids"])]
                
                segments:List[GSegment] = [GSegment(None, box, segment_tags.from_id(tag_id)) for box, tag_id in zip(record["data"]["segments"]["boxes"],
                                                                                                                   record["data"]["segments"]["tags"])]

            

                #nacteni obrazku
                img_path = Path(os.path.join(parent_folder,"images",file_name))
                if not img_path.exists():
                    continue

                items_quantity = invoice_enhancer.items_quantity(segments)
                items_quantity = max(2, items_quantity)
                    
                supp = invoice_generator.generate_company()
                cust = invoice_generator.generate_company()
                bank = banks_[random.randrange(0, len(banks_))]
                payment = payments[random.randrange(0, len(payments))]
                items, total_price, total_vat = invoice_generator.generate_items(items_quantity)
                invoice_number = invoice_generator.generate_invoice_number()
                variable_symbol = invoice_generator.generate_variable_symbol(invoice_number)
                const_symbol = invoice_generator.generate_const_symbol()
                bank_account_number, IBAN = invoice_generator.generate_bank_account(bank)
                issue_date, taxable_supply_date, due_date = invoice_generator.generate_invoice_dates()

                inv = DInvoice(invoice_number=invoice_number,
                    variable_symbol=variable_symbol,
                    bank_account_number=bank_account_number,
                    IBAN=IBAN, const_symbol=const_symbol, issue_date=issue_date,
                    taxable_supply_date=taxable_supply_date, due_date=due_date, 
                    supplier=supp, customer=cust, total_vat=total_vat, total_price=total_price,
                    bank_account=bank, payment_type=payment, items=items, rounding=0)

                inv.load_tokens(tokens)
                inv.load_spans(spans)
                inv.load_segments(segments)

                img = Image.open(img_path).convert("RGB")
                img_draw = Draw(img)

                invoice_enhancer.draw_spans(inv, img_draw, img)

                invoice_enhancer.draw_segments(inv, img_draw, img)
        
                #invoice_enhancer.display_bounding_boxes(inv, img_draw, True)

                new_file_name = f"{file_name.replace(".png", "")}_enhanced_{"_".join(str(datetime.now()).split(" "))}.png"
                enhanced_img_path = Path(os.path.join(images_path, new_file_name)) 
                
                img = inv.post_process(img)
                img.save(enhanced_img_path)

                #export faktury

                donut_metada_path = os.path.join(save_folder, "metadata_donut.jsonl")
                layoutlmv3_metada_path = os.path.join(save_folder, "metadata_layoutlmv3.jsonl")
                coco_metadata_path = os.path.join(save_folder, "metadata_coco.json")
                yolo_path = labels_path

                # --- 3. Zápis do DONUT (JSONL) ---
                donut_gt = {"gt_parse": inv.to_json_donut(False)}
                donut_output = {
                    "file_name": new_file_name,
                    "ground_truth": donut_gt
                }
                with open(donut_metada_path, "a", encoding="utf-8") as f_donut:
                    f_donut.write(json.dumps(donut_output, ensure_ascii=False) + "\n")

                # --- 4. Zápis do LAYOUTLMv3 (JSONL) ---
                layout_data = inv.to_json_layoutlmv3(enhanced_img_path)
                layout_output = {
                    "file_name": new_file_name,
                    "data": layout_data
                }
                with open(layoutlmv3_metada_path, "a",encoding="utf-8") as f_layout:
                    f_layout.write(json.dumps(layout_output, ensure_ascii=False) + "\n")

                # --- 5. Sběr dat pro COCO ---
                coco_data = inv.to_json_coco(coco_metadata_path, new_file_name) 
                with open(coco_metadata_path, "w", encoding="utf-8") as f_coco:
                    f_coco.write(json.dumps(coco_data, ensure_ascii=False, indent=4))
                    
                # --- 6. YOLO formát ---
                yolo_data = inv.to_json_yolo()
                yolo_label_path = os.path.join(yolo_path, f"{new_file_name.replace(".png", ".txt")}") 
                with open(yolo_label_path, "w", encoding="utf-8") as f_yolo:
                    f_yolo.write(yolo_data)


    def display_bounding_boxes(invoice:DInvoice, draw:ImageDraw, tokens:bool = False, spans:bool = False,
                               segments:bool = True):
        tokens_color = (0,0,0)
        spans_color = (0,255,0)
        segments_color = (255,0,255)

        if tokens:
            for token in invoice._tokens:
                if token.tag == token_tags.O:
                    continue

                draw.rectangle(token.b_box, outline=tokens_color)
                draw.text(token.b_box, text=token.tag.text, fill="red")

        if spans:
            for span in invoice._spans:
                if span.tag == span_tags.O:
                    continue
                draw.rectangle(span.b_box, outline=spans_color)

        if segments:
            for segment in invoice._segments:
                draw.rectangle(segment.b_box,outline=segments_color)

    def items_quantity(segments:List[GSegment]):
        line_height = 50
        items_count = math.inf
        
        for segment in segments:
            if segment.tag == segment_tags.ITEMS_BLOCK:
                items_count = min(items_count, (int)((segment.b_box[3] - segment.b_box[1])/line_height))
    
        if items_count == math.inf:
            return 0

        return items_count

    def sample_background(img:Image.Image, bbox, sample_per_line=20, lines=1)->tuple[int, int, int]:
        return (255,255,255)

    def draw_spans(invoice:DInvoice, draw:ImageDraw, img:Image.Image):
        
        draw_color = (0,0,0)
        fill_color = (255,255,255)
        
        spans_copy = list(invoice._spans)

        for span in spans_copy:

            if span.tag == span_tags.O:
                continue

            color = invoice_enhancer.sample_background(img, span.b_box)

            draw.rectangle(span.b_box, fill=fill_color) #pro jistotu ještě vždy vyčistíme
            tag = span.tag
            text = ""
            
            if tag == span_tags.INVOICE_NUMBER:
                text = invoice.invoice_number
            elif tag == span_tags.SUPPLIER_REGISTER_ID:
                text = invoice.supplier.register_id
            elif tag == span_tags.SUPPLIER_TAX_ID:
                text = invoice.supplier.tax_id
            elif tag == span_tags.CUSTOMER_REGISTER_ID:
                text = invoice.customer.register_id
            elif tag == span_tags.CUSTOMER_TAX_ID:
                text = invoice.customer.tax_id
            elif tag == span_tags.ISSUE_DATE:
                text = invoice.issue_date
            elif tag == span_tags.TAXABLE_SUPPLY_DATE:
                text = invoice.taxable_supply_date
            elif tag == span_tags.DUE_DATE:
                text = invoice.due_date
            elif tag == span_tags.PAYMENT_TYPE:
                text = invoice.payment_type
            elif tag == span_tags.BANK_ACCOUNT_NUMBER:
                text = invoice.bank_account_number
            elif tag == span_tags.IBAN:
                text = invoice.IBAN
            elif tag == span_tags.BIC:
                text = invoice.bank_account.BIC
            elif tag == span_tags.VARIABLE_SYMBOL:
                text = invoice.variable_symbol
            elif tag == span_tags.CONST_SYMBOL:
                text = invoice.const_symbol
            elif tag == span_tags.TOTAL:
                text = fmt_money(invoice.total_price)
            else:
                continue
            
            #adaptivní vykreslování 

            width = abs(span.b_box[2]-span.b_box[0])

            font, _ = fit_line_bounding_box_font(text, width, font_path=invoice._f10.path)
            if not font:
                font = invoice._f10

            invoice._text(draw, (span.b_box[0], span.b_box[1]),
                          text=str(text), fill=draw_color, font=font, span_tag=tag)

            #smažeme všechny tokeny spanu
            for token_id in span.tokens:
                token:GToken = invoice.get_token_by_id(token_id)
                invoice.remove_token(token)
            
            invoice.remove_span(span)


    def draw_segments(invoice:DInvoice, draw:ImageDraw, img:Image.Image):
        
        comapany_block_chance = 0.5 #upřednosňujeme spíše pozměnění pouze informací před změnou bloku celého
        draw_color = (255,255,255)
        
        invoice._segments.sort(key=lambda segment: segment.tag.code, reverse=True)

        for segment in invoice._segments:
            tag = segment.tag
            color = invoice_enhancer.sample_background(img, segment.b_box)

            if tag == segment_tags.SUPPLIER_INNER_BLOCK:
                draw.rectangle(segment.b_box, fill=color) #pro jistotu ještě vždy vyčistíme
                invoice_enhancer.remove_tokens_hide_by_segment(invoice, draw, segment)

                invoice_enhancer.draw_supplier_inner_block(segment.b_box, draw, invoice)

            elif tag == segment_tags.SUPPLIER_BLOCK and random.random() < comapany_block_chance:
                draw.rectangle(segment.b_box, fill=color) #pro jistotu ještě vždy vyčistíme
                invoice_enhancer.remove_tokens_hide_by_segment(invoice, draw, segment)

                invoice_enhancer.draw_supplier_block(segment.b_box, draw, invoice)

            elif tag == segment_tags.CUSTOMER_BLOCK and random.random() < comapany_block_chance:
                draw.rectangle(segment.b_box, fill=color) #pro jistotu ještě vždy vyčistíme
                invoice_enhancer.remove_tokens_hide_by_segment(invoice, draw, segment)

                invoice_enhancer.draw_customer_block(segment.b_box, draw, invoice)

            elif tag == segment_tags.CUSTOMER_INNER_BLOCK:
                draw.rectangle(segment.b_box, fill=color) #pro jistotu ještě vždy vyčistíme
                invoice_enhancer.remove_tokens_hide_by_segment(invoice, draw, segment)

                invoice_enhancer.draw_customer_inner_block(segment.b_box, draw, invoice)

            elif tag == segment_tags.ITEMS_BLOCK:
                draw.rectangle(segment.b_box, fill=color) #pro jistotu ještě vždy vyčistíme
                invoice_enhancer.remove_tokens_hide_by_segment(invoice, draw, segment)

                invoice_enhancer.draw_items_block(segment.b_box, draw, invoice)

            elif tag == segment_tags.VAT_BLOCK:
                draw.rectangle(segment.b_box, fill=color) #pro jistotu ještě vždy vyčistíme
                invoice_enhancer.remove_tokens_hide_by_segment(invoice, draw, segment)

                invoice_enhancer.draw_vat_block(segment.b_box, draw, invoice)


    def draw_supplier_inner_block(bbox, draw:ImageDraw, invoice: DInvoice):
        words_to_display = " ".join([invoice.supplier.name, invoice.supplier.type.value, invoice.supplier.address, invoice.supplier.country.value,
                                     invoice.supplier.phone]).split(" ")

        invoice_enhancer.draw_company_inner_block(words_to_display, bbox, draw, invoice)

    def draw_supplier_block(bbox, draw:ImageDraw, invoice: DInvoice):
        company_block_templates = [company_c]
        company_block:invoice_component = random.choice(company_block_templates)

        company_block.draw(invoice, draw, bbox[0], bbox[1], width=bbox[2]-bbox[0], height=bbox[3]-bbox[1], supplier=True)

    def draw_customer_block(bbox, draw:ImageDraw, invoice: DInvoice):
        company_block_templates = [company_c]
        company_block:invoice_component = random.choice(company_block_templates)

        company_block.draw(invoice, draw, bbox[0], bbox[1], width=bbox[2]-bbox[0], height=bbox[3]-bbox[1], supplier=False)
    
    def draw_customer_inner_block(bbox, draw:ImageDraw, invoice: DInvoice):
        words_to_display = " ".join([invoice.customer.name, invoice.customer.type.value, invoice.customer.address]).split(" ")

        invoice_enhancer.draw_company_inner_block(words_to_display, bbox, draw, invoice)
    
    def draw_items_block(bbox, draw:ImageDraw, invoice: DInvoice):
        total_block_templates = [table_a, table_b]
        total_block:invoice_component = random.choice(total_block_templates)

        total_block.draw(inv=invoice, d=draw, x=bbox[0],y=bbox[1], width=bbox[2]-bbox[0], height=bbox[3]-bbox[1])
    
    def draw_vat_block(bbox, draw:ImageDraw, invoice: DInvoice):
        vat_block_templates = [vat_a, vat_b, vat_c]
        vat_block:invoice_component = random.choice(vat_block_templates)

        vat_block.draw(inv=invoice, d=draw, x=bbox[0],y=bbox[1], width=bbox[2]-bbox[0], height=bbox[3]-bbox[1])

    #----------------------------UTILITY---------------------------
    def remove_tokens_hide_by_segment(invoice:DInvoice, draw:ImageDraw, segment:GSegment):
        draw_color = (255,255,255)
        tokens_in_segments: List[GToken] = invoice.get_tokens_in_bounding_box(segment.b_box)

        for token in tokens_in_segments:
            #najdu jestli je token v nějakém spanu
            span:GSpan = invoice.get_span_by_containing_token(token)
            if(span):
                draw.rectangle(span.b_box, fill=draw_color)
                
            invoice.remove_token(token)
            invoice.remove_span(span)


    def draw_company_inner_block(words:List[str], bbox, draw:ImageDraw, invoice:DInvoice):
        draw_color = (0,0,0)

        x, y = bbox[0], bbox[1]
        end_x, end_y = bbox[2], bbox[3]

        box_width = abs(end_x - x)

        font, _ , space = fit_text_bounding_box_font(words, bbox, font_path=invoice._f10.path)
        if not font:
            return

        line_height, _ = font.getmetrics()

        for word in words:
            
            word_length:int = text_width(word, font)
            word_end_x = x + word_length
            if(word_end_x > end_x):
                x = bbox[0]
                y += line_height + space
            invoice._text(draw=draw, poss=(x,y), text=word, fill=draw_color, font=font, span_tag=span_tags.O)

            x = x + word_length + text_width(" ", font)
