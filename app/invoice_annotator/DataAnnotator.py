from invoice_annotator.windows.MainWindow import MainWindow

#hlavni aplikace
class DataAnnotator:


    def __init__(self, *args, **kwargs):
        self.window = MainWindow()
        
    
    def run(self)->None:
        self.window.mainloop()
