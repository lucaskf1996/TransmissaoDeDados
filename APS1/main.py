# File to make an interface for working with the applications
import tkinter as tk
import tkinter.filedialog as tkfd


#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
# serialName = "COM4"                  # Windows(variacao de)

from enlace import *
import time
import os
import math

class Application1:
    def __init__(self, master=None):
        self.master = master
        self.widget1 = tk.Frame(self.master)
        self.widget1.pack()
        self.game = tk.Label(self.widget1, text = 'Por favor, selecione uma imagem para ser enviada:')
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
        mode = int(input("digite 1 ou 2 para escolher qual dos arduinos enviará o arquivo: "))

        ask_file = tk.Tk()
        ask_file.geometry("900x120")
        app_1 = Application1(ask_file)
        ask_file.mainloop()

        saveImage1 = os.getcwd() + "//imgs1//received.png"
        saveImage2 = os.getcwd() + "//imgs2//received.png"

        arduino1 = "COM8"
        arduino2 = "COM5"

        if mode==1:

            print("Estabelecendo enlace client:")
            comClient = enlace(arduino1)
            comClient.enable()
            print("Enlace e comunicação client habilitada!")
            print("")
            print("Estabelecendo enlace server:")
            comServer = enlace(arduino2)
            comServer.enable()
            print("Enlace e comunicação server habilitada!")

        elif mode==2:

            print("Estabelecendo enlace client:")
            comClient = enlace(arduino2)
            comClient.enable()
            print("Enlace e comunicação client habilitada!")
            print("")
            print("Estabelecendo enlace server:")
            comServer = enlace(arduino1)
            comServer.enable()
            print("Enlace e comunicação server habilitada!")


        envio = time.time()
        with open(app_1.data, "rb") as file1:
            clientBuffer = file1.read()

        n_bytes = math.floor((math.log2(len(clientBuffer))/8)) + 1
        len_bytes = (len(clientBuffer).to_bytes(n_bytes,'little'))
        clientBuffer = bytes([n_bytes]) + len_bytes + clientBuffer
        # print("clientBuffer:" + str(clientBuffer))

        # print("")

        # print("Tamanho da mensagem:" + str(len(clientBuffer)))

        print("")

        comClient.sendData(clientBuffer)
        print("Client data sent!")
        
        print("")
        time.sleep(0.1)

        sizeOfSize, nRx = comServer.getData(1)
        # sizeOfSize = int.from_bytes(sizeOfSize,"little")
        # print("Size of Size:" + str(int.from_bytes(sizeOfSize,"little")))

        sizeOfImage, nRx = comServer.getData(int.from_bytes(sizeOfSize,"little"))
        # sizeOfImage = int.from_bytes(sizeOfImage,"little")
        print("Tamanho da Imagem:" + str(int.from_bytes(sizeOfImage,"little")))
        # print("")
        imageData, nRx = comServer.getData(int.from_bytes(sizeOfImage,"little"))
        # print(str(imageData[0:100]) + "...")

        if mode == 1:
            with open(saveImage2, "wb") as file2:
                file2.write(imageData)
        elif mode == 2:
            with open(saveImage1, "wb") as file2:
                file2.write(imageData)
        print("")
        print("Transmicao terminada")
        print("")

        print("-----------------------------------------")
        print("Iniciando confirmacao dos dados recebidos")
        print("-----------------------------------------")
        returnSize = sizeOfSize + sizeOfImage
        print("Enviando tamanho do dado recebido ({}):".format(str(returnSize)))
        comServer.sendData(returnSize)
        print("")
        sizeOfSizeReturn, nRx = comClient.getData(1)
        sizeOfImageReturn, nRx = comClient.getData(int.from_bytes(sizeOfSizeReturn,"little"))
        print("Confirmação do tamanho: {}".format(int.from_bytes(sizeOfImageReturn,"little")))
        print("")
        recebimento = time.time()
        # print(envio)
        # print(recebimento)
        print("{0:.3f}".format(recebimento - envio), "segundos para envio e recebimento completo")
        print("")
        velocidadeTransmissao = int.from_bytes(sizeOfImage,"little")/(recebimento-envio)
        print("\nTaxa de transmissao: {} bytes/segundos".format(velocidadeTransmissao))
        # print("")
        # Encerra comunicação
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        comServer.disable()
        comClient.disable()
    except Exception as e:
        print("Occoreu um erro!")
        print("")
        print(e)
        print("")
        comServer.disable()
        comClient.disable()
