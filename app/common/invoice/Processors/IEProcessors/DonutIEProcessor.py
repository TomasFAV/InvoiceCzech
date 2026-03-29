from collections import defaultdict
from enum import Enum
import json
from pathlib import Path
from typing import Any
from common.enumerates.SpanTag import SPAN_TAGS_TO_IGNORE, SpanTag
from common.invoice.models.InvoiceData import InvoiceData
from common.invoice.models.Invoice import Invoice
from common.invoice.OperationResult import OperationResult
from common.invoice.Processors.IEProcessors.IEProcessor import IEProcessor

class DonutIEConfig(Enum):
    FROM_INVOICE_DATA = "FROM_INVOICE_DATA"
    FROM_INVOICE_DATA_WITH_CHECK = "FROM_INVOICE_DATA_WITH_CHECK"
    FROM_SPANS = "FROM_SPANS"    

class DonutIEProcessor(IEProcessor):


    def _export(self, invoice:Invoice|None = None, original_data:InvoiceData|None = None, option: DonutIEConfig = DonutIEConfig.FROM_SPANS)->dict[str, Any]:
        result: OperationResult = OperationResult(False)
        
        if(option == DonutIEConfig.FROM_INVOICE_DATA):
            result = self.__to_json_donut_from_invoice_data(original_data)
        elif(option == DonutIEConfig.FROM_INVOICE_DATA_WITH_CHECK):
            result = self.__to_json_donut_from_invoice_data_with_check(invoice, original_data)
        elif(option == DonutIEConfig.FROM_SPANS):
            result = self.__to_json_donut_from_spans(invoice)

        if(not result.ok):
            if isinstance(result.passed_value, str):
                raise result.passed_value
            else:
                raise "Something went wrong, DonutExport"
            
        return result.passed_value

    def _import(self, invoice_data:InvoiceData, donut_file_path: Path, invoice_file_path:Path)->bool:
        """
            Natáhne hodnoty do invoice_data
        """
        result:OperationResult = self.__data_from_donut(invoice_data, donut_file_path, invoice_file_path)

        if(result.ok):
            return result.passed_value
        
        return False    
    
    def __data_from_donut(self, invoice_data:InvoiceData, donut_file_path: Path, invoice_file_path:Path) -> OperationResult:
        
        """Načte json informace z donut souboru pro file_path fakturu"""

        with open(donut_file_path, "r", encoding="utf-8") as f:
            for line in f:
                raw_data = json.loads(line)

                if raw_data["file_name"] != invoice_file_path.name:
                    continue
                
                ground_truth:dict = raw_data.get("ground_truth", None)
                if not ground_truth or not isinstance(ground_truth, dict):
                    return False
                
                data:dict = ground_truth.get("gt_parse", None)
                if not data or not isinstance(data, dict):
                    return False


                invoice_data.invoice_number = data.get("invoice_number", "")
                
                invoice_data.supplier.register_id = data.get("supp_register_id", "")
                invoice_data.supplier.tax_id = data.get("supp_tax_id", "")

                invoice_data.customer.register_id = data.get("cust_register_id", "")
                invoice_data.customer.tax_id = data.get("cust_tax_id", "")

                invoice_data.issue_date = data.get("issue_date", "")
                invoice_data.taxable_supply_date = data.get("taxable_supply_date", "")
                invoice_data.due_date = data.get("due_date", "")

                invoice_data.payment_type = data.get("payment_type", "")
                invoice_data.bank_account_number = data.get("bank_account_number", "")
                invoice_data.bank_account.BIC = data.get("bic", "")
                invoice_data.IBAN = data.get("iban", "")
                invoice_data.variable_symbol = data.get("variable_symbol", "")
                invoice_data.const_symbol = data.get("const_symbol", "")
                invoice_data.total_price = data.get("total", "")        

                return OperationResult(True, True)
        
        return OperationResult(True, False)

    def __to_json_donut_from_invoice_data(self, original_data:InvoiceData)->OperationResult:
        if original_data is None:
            return OperationResult(False, "InvoiceData cannot be null.")
        return OperationResult(True, original_data.to_dict())


    def __to_json_donut_from_invoice_data_with_check(self, invoice:Invoice, original_data:InvoiceData)->OperationResult:
        """
        Vrací dict pro donut, v případě, že se předají original_data, tak vytvoří dict na základě nich,
        v opačném případě vytvoří dict ze spans faktury
        """
        if invoice is None or original_data is None:
            return OperationResult(False, "Invoice and InvoiceData cannot be null.")

        output_json = defaultdict(str)  
        temp_json = original_data.to_dict()        

        for span_tag in list(SpanTag):
            if span_tag in SPAN_TAGS_TO_IGNORE or span_tag == SpanTag.O:
                continue
            output_json[span_tag.text] = ""

        #zkontroluji, zda jsou na faktuře označeny
        for span in invoice._spans:
            if(span.tag in SPAN_TAGS_TO_IGNORE) or span.tag == SpanTag.O:
                continue
            
            output_json[span.tag.text] = temp_json[span.tag.text]

        return OperationResult(True, output_json)


    def __to_json_donut_from_spans(self, invoice:Invoice)->OperationResult:
        #projdu tokeny a pokud je tam span s tagem různým od 0 a neni jeho bounding box mimo, tak ho pridam do slovniku
        output_json = dict()
        
        for span_tag in list(SpanTag):
            if span_tag in SPAN_TAGS_TO_IGNORE:
                continue
            output_json[span_tag.text] = ""

        for span in invoice._spans:
            if(span.tag in SPAN_TAGS_TO_IGNORE):
                output_json[span.tag.text] = ""
                continue
            
            output_json[span.tag.text] = "".join([invoice.get_token_by_id(token_id).text for token_id in span.tokens]) 
            if span.tag == SpanTag.PAYMENT_TYPE:
                output_json[span.tag.text] = " ".join([invoice.get_token_by_id(token_id).text for token_id in span.tokens]) 
    
        output_json.pop("vat", None)
        output_json.pop("vat_base", None)
        output_json.pop("vat_percentage", None)
        output_json.pop("o", None)          

        return OperationResult(True, output_json)