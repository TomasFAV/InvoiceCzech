from tkinter import Tk, font, Frame
from invoice_annotator.controller.ExportPageController import ExportPageController
from invoice_annotator.view.pages.ExportPage import ExportPage
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
class MainWindow(IMainWindow):


    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.title("NER Annotator")
        self.geometry("1280x720")
        self.minsize(900, 600)
        
        self.frames = {}

        self.title_font = font.Font(family='Helvetica', size=18, weight="bold", slant="italic")

        self.__build_container()
        self.show_frame("HomePage")


    def __build_container(self)-> None:
        self.container = Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        for page, controller in [(HomePage, HomePageController), (ExportPage, ExportPageController)]:
            page:View = cast(View, page)
            controller= controller()
            
            page_name = page.__name__
            frame = page(self, parent=self.container, controller=controller)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        frame:View = self.frames[page_name]
        frame.tkraise()

        frame.full_redraw()

    
    def run(self)->None:
        self.mainloop()
