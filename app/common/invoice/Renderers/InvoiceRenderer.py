import math
import random
from typing import List

import numpy as np
from common.enumerates.SegmentTag import SegmentTag
from common.invoice.models import GToken
from invoices_generator.templates.components.bodies.TableA import TableA
from invoices_generator.templates.components.bodies.TableB import TableB
from invoices_generator.templates.components.suppliers_customers.CompanyA import CompanyA
from invoices_generator.templates.components.suppliers_customers.CompanyB import CompanyB
from invoices_generator.templates.components.suppliers_customers.CompanyC import CompanyC
from invoices_generator.templates.components.vats.VatA import VatA
from invoices_generator.templates.components.vats.VatB import VatB
from invoices_generator.templates.components.vats.VatC import VatC
from common.enumerates.SpanTag import SpanTag
from invoices_generator.utility.utils import fit_line_bounding_box_font, fit_text_bounding_box_font, fmt_money, text_width
from invoices_generator.core.InvoiceComponent import InvoiceComponent
from common.Span import Span
from common.invoice.OperationResult import OperationResult
from common.invoice.Renderers.InvoicePostProcessor import InvoicePostProcessor
from common.invoice.Renderers.TextRenderer import TextRenderer
from common.invoice.models.Invoice import Invoice
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.models.InvoiceTemplate import InvoiceTemplate
from PIL.ImageDraw import ImageDraw

class InvoiceRenderer:
    def __init__(self):
        self.text_renderer: TextRenderer = TextRenderer()
        self.post_processor: InvoicePostProcessor = InvoicePostProcessor()
        pass

    
    #------------------------------VYTVOŘENÍ FAKTURY NA ZÁKLADĚ DAT A ŠABLONY------------------------------------------

    def render(self, data: InvoiceData, template: InvoiceTemplate) -> OperationResult:
        invoice: Invoice = Invoice()
        

        template.render(textRenderer=self.text_renderer, data=data, invoice=invoice) #vytvoří fakturu spolu s obrázkem
        self.post_processor.post_process(invoice) #augmentuje fakturu(bboxy + obrázek)
        
        return OperationResult(True, invoice)
    
    #-----------------------------VYKRESLOVÁNÍ DO JIŽ EXISTUJÍCÍCH FAKTUR-----------------------------------

    def render_component(self, area:tuple[int,int,int,int], data:InvoiceData, invoice:Invoice, component:InvoiceComponent, *args, **kwargs):
        invoice.remove_objects(area) #odstraníme všechno v dané oblasti
        ImageDraw(invoice.image).rectangle(area, fill=(255,255,255)) #vyčistím si oblast

        component.render(self.text_renderer, data, invoice, area[0], area[1], width=area[2]-area[0], height=area[3]-area[1], *args, **kwargs) #vykreslím komponentu

    def render_text(self, words:List[str], area:tuple[int,int,int,int], invoice:Invoice):
        draw_color = (0,0,0)
        draw = ImageDraw(invoice.image)

        x, y = area[0], area[1]
        end_x, end_y = area[2], area[3]

        font, _ , space = fit_text_bounding_box_font(words, area, font_path=self.text_renderer._f10.path)
        if not font:
            return

        line_height, _ = font.getmetrics()

        for word in words:
            
            word_length:int = text_width(word, font)
            word_end_x = x + word_length
            if(word_end_x > end_x):
                x = area[0]
                y += line_height + space
            self.text_renderer._text(invoice, draw=draw, poss=(x,y), text=word, fill=draw_color, font=font, span_tag=SpanTag.O)

            x = x + word_length + text_width(" ", font)

    def render_spans(self, data:InvoiceData, invoice:Invoice):
        draw_color = (0,0,0)
        fill_color = (255,255,255)
        
        spans_copy = list(invoice._spans)
        draw = ImageDraw(invoice.image)

        for span in spans_copy:

            if span.tag == SpanTag.O:
                continue

            draw.rectangle(span.b_box, fill=fill_color) #pro jistotu ještě vždy vyčistíme
            tag = span.tag
            text = ""
            
            if tag == SpanTag.INVOICE_NUMBER:
                text = data.invoice_number
            elif tag == SpanTag.SUPPLIER_REGISTER_ID:
                text = data.supplier.register_id
            elif tag == SpanTag.SUPPLIER_TAX_ID:
                text = data.supplier.tax_id
            elif tag == SpanTag.CUSTOMER_REGISTER_ID:
                text = data.customer.register_id
            elif tag == SpanTag.CUSTOMER_TAX_ID:
                text = data.customer.tax_id
            elif tag == SpanTag.ISSUE_DATE:
                text = data.issue_date
            elif tag == SpanTag.TAXABLE_SUPPLY_DATE:
                text = data.taxable_supply_date
            elif tag == SpanTag.DUE_DATE:
                text = data.due_date
            elif tag == SpanTag.PAYMENT_TYPE:
                text = data.payment_type
            elif tag == SpanTag.BANK_ACCOUNT_NUMBER:
                text = data.bank_account_number
            elif tag == SpanTag.IBAN:
                text = data.IBAN
            elif tag == SpanTag.BIC:
                text = data.bank_account.BIC
            elif tag == SpanTag.VARIABLE_SYMBOL:
                text = data.variable_symbol
            elif tag == SpanTag.CONST_SYMBOL:
                text = data.const_symbol
            elif tag == SpanTag.TOTAL:
                text = fmt_money(data.total_price)
            else:
                continue
            
            #adaptivní vykreslování 

            width = abs(span.b_box[2]-span.b_box[0])

            font, _ = fit_line_bounding_box_font(text, width, font_path=self.text_renderer._f10.path)
            if not font:
                font = self.text_renderer._f10

            self.text_renderer._text(invoice, draw, (span.b_box[0], span.b_box[1]),
                          text=str(text), fill=draw_color, font=font, span_tag=tag)

            #smažeme všechny tokeny spanu
            for token_id in span.tokens:
                token:GToken = invoice.get_token_by_id(token_id)
                invoice.remove_token(token)
            
            invoice.remove_span(span)

    def render_segments(self, data:InvoiceData, invoice:Invoice):
        comapany_block_chance = 0.5 #upřednosňujeme spíše pozměnění pouze informací před změnou bloku celého
        draw_color = (0,0,0)
        fill_color = (255,255,255)
        
        invoice._segments.sort(key=lambda segment: segment.tag.code, reverse=True)
        draw = ImageDraw(invoice.image)

        for segment in invoice._segments:
            tag = segment.tag

            if tag == SegmentTag.SUPPLIER_INNER_BLOCK:
                draw.rectangle(segment.b_box, fill=fill_color) #pro jistotu ještě vždy vyčistíme
                invoice.remove_objects(segment.b_box)
                words_to_display = " ".join([data.supplier.name, data.supplier.type.value, data.supplier.address, data.supplier.country.value,
                                     data.supplier.phone]).split(" ")

                self.render_text(words_to_display, segment.b_box, invoice)

            elif tag == SegmentTag.SUPPLIER_BLOCK and random.random() < comapany_block_chance:
                draw.rectangle(segment.b_box, fill=fill_color) #pro jistotu ještě vždy vyčistíme
                invoice.remove_objects(segment.b_box)

                self.render_component(segment.b_box, data, invoice, random.choice([CompanyA, CompanyB, CompanyC]))

            elif tag == SegmentTag.CUSTOMER_BLOCK and random.random() < comapany_block_chance:
                draw.rectangle(segment.b_box, fill=fill_color) #pro jistotu ještě vždy vyčistíme
                invoice.remove_objects(segment.b_box)

                self.render_component(segment.b_box, data, invoice, random.choice([CompanyA, CompanyB, CompanyC]))

            elif tag == SegmentTag.CUSTOMER_INNER_BLOCK:
                draw.rectangle(segment.b_box, fill=fill_color) #pro jistotu ještě vždy vyčistíme
                invoice.remove_objects(segment.b_box)
                words_to_display = " ".join([data.customer.name, data.customer.type.value, data.customer.address, data.customer.country.value,
                                     data.customer.phone]).split(" ")

                self.render_text(words_to_display,segment.b_box, invoice)

            elif tag == SegmentTag.ITEMS_BLOCK:
                draw.rectangle(segment.b_box, fill=fill_color) #pro jistotu ještě vždy vyčistíme
                invoice.remove_objects(segment.b_box)

                self.render_component(segment.b_box, data, invoice, random.choice([TableA, TableB]))

            elif tag == SegmentTag.VAT_BLOCK:
                draw.rectangle(segment.b_box, fill=fill_color) #pro jistotu ještě vždy vyčistíme
                invoice.remove_objects(segment.b_box)

                self.render_component(segment.b_box, data, invoice, random.choice([VatA, VatB, VatC]))


    def enhandce(self, invoice_data:InvoiceData, invoice:Invoice):
        self.render_spans(invoice_data, invoice)
        self.render_segments(invoice_data, invoice)
        self.post_processor.post_process(invoice)