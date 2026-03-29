from client.windows.MainWindow import MainWindow

#hlavni aplikace
class Client:


    def __init__(self, *args, **kwargs):
        self.window = MainWindow()
        
    
    def run(self)->None:
        self.window.mainloop()
