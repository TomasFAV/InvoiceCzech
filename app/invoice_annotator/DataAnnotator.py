from tkinter import Tk, font, Frame
from invoice_annotator.windows.MainWindow import MainWindow
from invoice_annotator.view.interfaces.IDataAnnotator import IMainWindow
from invoices_generator.core.enumerates.segment_tags import segment_tags
from invoice_annotator.controller.Controller import Controller
from invoice_annotator.controller.HomePageController import HomePageController
from invoice_annotator.view.pages.HomePage import HomePage
from invoice_annotator.view.View import View
from invoices_generator.core.enumerates.relationship_types import relationship_types
from invoices_generator.core.enumerates.span_tags import span_tags
from invoices_generator.core.enumerates.token_tags import token_tags
from typing import cast

#hlavni aplikace
class DataAnnotator:


    def __init__(self, *args, **kwargs):
        self.window = MainWindow()
        
    
    def run(self)->None:
        self.window.mainloop()
