from tkinter import Tk, font, Frame
from common.Session import Session
from common.interfaces.IMainWindow import IMainWindow
from common.controller.Controller import Controller
from client.controller.HomePageController import HomePageController
from client.view.pages.HomePage import HomePage
from common.view.View import View
from typing import cast

#hlavni aplikace
class MainWindow(IMainWindow):


    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        self.title("Invoice preprocessor")
        self.geometry("1280x720")
        self.minsize(900, 600)
        
        self.frames = {}

        self.title_font = font.Font(family='Helvetica', size=18, weight="bold", slant="italic")

        self.session:Session = Session()

        self.__build_container()
        self.show_frame("HomePage")


    def __build_container(self)-> None:
        self.container = Frame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        for page, controller in [(HomePage, HomePageController)]:
            page:View = cast(View, page)
            controller:Controller = cast(Controller, controller)
            controller:Controller = controller(self.session)
            
            page_name = page.__name__
            frame:View = page(self, parent=self.container, controller=controller)
            self.frames[page_name] = frame

            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, page_name):
        '''Show a frame for the given page name'''
        if page_name not in self.frames:
            raise "Unknown page_name in method show_frame"

        frame:View = self.frames[page_name]
        frame.tkraise()

        frame.boot_up()
        frame.full_redraw()

    
    def run(self)->None:
        self.mainloop()
