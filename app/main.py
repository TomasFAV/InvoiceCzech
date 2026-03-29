from client.Client import Client
from invoices_generator.InvoiceEnhancer import InvoiceEnhancer
from invoice_annotator.DataAnnotator import DataAnnotator
from invoices_generator.InvoiceGenerator import InvoiceGenerator

def main()->None:
    #app = DataAnnotator()
    app = Client()
    
    app.run()

    #InvoiceGenerator.generate(0, 0, 1)
    #InvoiceEnhancer.enhance("/home/tom-k/Desktop/Zpracovani_faktur/app/data/validation/metadata_layoutlmv3.jsonl", 5)

if __name__=="__main__":
    main()
