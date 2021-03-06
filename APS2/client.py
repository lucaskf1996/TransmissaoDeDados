import threading
from enlace import enlace
import stdMsgs
import time
import random

class Client:
    def __init__(self, port):
        self.com = enlace(port)
        time.sleep(3e-3)
        self.running = False
        self.threadActive = False
        self.thread = None
        self.buffer = {}
        self.codes = {
            "FAIL":stdMsgs.FAILMSG,
            "PASS":stdMsgs.SUCCESSMSG,
            "INTERNALCLIENTERROR":stdMsgs.CLIENTERRORMSG
        }

    def beginRunning(self):
        self.com.enable()        
        serverAlive = False
        while not serverAlive:
            print("==================================== \nBeginning client handshake: \n====================================\n")
            self.com.sendData(stdMsgs.HANDSHAKEMSG)
            print("Sending handshake (Now waiting for 5 seconds)")
            time.sleep(5)
            print("Checking for response")

            buff = self.com.rx.getBuffer(14)
            if len(buff) != 14:    
                print("The server hasn't responded yet...")
                j = input("Try again? (y/n): ")
                if(j.lower() in [" ", "y", ""]):
                    continue
                else:
                    serverAlive = False
                    break
            if buff == stdMsgs.SUCCESSMSG:
                print("Handshake Success!\n")
                serverAlive = True
            
            self.com.rx.clearBuffer()
        if not serverAlive:
            self.killProcess()
            return
        print("==================================== \nClient handshake finished. \n====================================\n")


    def reply(self, keyword):
        try:
            message = self.codes[keyword]
        except KeyError:
            message = self.codes["INTERNALCLIENTERROR"]
        
        self.com.sendData(message)

    def killProcess(self):
        self.com.disable()

    def sendDatagram(self, datagram):
        success = False
        counter = 0
        while not success:
            mess = datagram[:]

            # This is to introduce noise for testing. Ignore.
            # if random.randint(0,100) < 15:
            #     mess = mess[0:3] + bytes([0, 2]) + mess[5:]
            #     # print("\nRandom error has been introduced!\n")
            if datagram[4] == 2:
                datagram[4] = 3 


            self.com.sendData(mess)
            resp, nRx = self.com.getData(14)
            success = resp == stdMsgs.SUCCESSMSG
            if resp[9] == 4:
                return -1
            counter += 1
            if counter >= 100:
                return 0
        return 1

    def sendMessage(self, message):
        for i in message:
            verif = self.sendDatagram(i)
            if verif == 0 or verif == -1:
                return verif
            else:
                continue