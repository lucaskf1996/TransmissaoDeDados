# File to make an interface for working with the applications
import tkinter as tk
import tkinter.filedialog as tkfd


#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
# serialName = "COM4"                  # Windows(variacao de)

import time
import os
import math
from helper import Helper
from application import Application
import stdMsgs
import traceback
import numpy as np

class Application1:
    def __init__(self, master=None):
        self.master = master
        self.widget1 = tk.Frame(self.master)
        self.widget1.pack()
        self.game = tk.Label(self.widget1, text = 'Por favor, selecione um arquivo para ser enviado:')
        self.game["font"] = ("Verdana", "12", "bold")
        self.game.config(anchor=tk.CENTER)
        self.game.pack()
        self.button = tk.Button(self.widget1)
        self.button["text"] = "Escolher"
        self.button["font"] = ("Cambria", "16", "bold")
        self.button["width"] = 24
        self.button["command"] = self.get_image
        self.button.config(anchor=tk.CENTER)
        self.button.pack()
        self.got_img = False
    
    def get_image(self):
        file = tkfd.askopenfilename(title='Choose a file')
        if file != None:
            self.data = file
            self.master.destroy()

if __name__ == "__main__":
    try:
        
        helper = Helper()

        # Interface do Tkinter para pegar arquivo a ser enviado.
        ask_file = tk.Tk()
        ask_file.geometry("900x120")
        app_1 = Application1(ask_file)
        ask_file.mainloop()
        readFile, saveFile = helper.buildPaths(app_1.data)
        # Protocol start:
        # ===========================================

        with open(readFile, "rb") as File:
            message = File.read()

        server = Application("COM8")
        client = Application("COM5")
        server.serverRun(saveFile, 2)
        client.clientRun(1, 2, message, 1)

        server.saveLog("Server")
        client.saveLog("Client")
        server.killServer()
        client.killClient()
    except Exception as e:
        print("\nOccoreu um erro!")
        print("")
        traceback.print_exc()
        print("")
        server.saveLog("Server")
        client.saveLog("Client")
        server.killServer()
        client.killClient()
