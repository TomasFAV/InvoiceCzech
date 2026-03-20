from invoices_generator.invoice_enhancer import invoice_enhancer
from invoice_annotator.DataAnnotator import DataAnnotator
from invoices_generator.invoice_generator import invoice_generator
from ie_engine.enumerates.engines import engines

def main()->None:
    app = DataAnnotator()
    app.run()

    #invoice_generator.generate(0, 0, 600)
    
    #invoice_enhancer.enhance("/home/tom-k/Desktop/faktury/training/ManualyAnotatedInvoices/metadata_layoutlmv3.jsonl", 5)

if __name__=="__main__":
    main()
