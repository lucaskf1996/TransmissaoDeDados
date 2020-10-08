import threading
from enlace import enlace
import stdMsgs
import time
from helper import Helper
import random
import numpy as np
import crcmod
import datetime

class Application:
    def __init__(self, port):
        self.com = enlace(port)
        time.sleep(3e-3)
        self.running = False
        self.threadActive = False
        self.thread = None      
        self.serverIDNum = None
        self.sensorIDNum = None  
        self.helper = Helper()
        self.contador = 1
        self.messages = {}
        self.lastSuccPkg = None
        self.dataID = None
        self.numPkgs = None
        self.log = "Log do "

        ################################
        ####### Client Variables #######
        ################################


        ################################
        ####### Server Variables #######
        ################################

        self.saveFile = None
        self.ocioso = True
        self.clientAlive = True
        self.handshakeCheck = 0

    def checkEOP(self, EOP):
        return EOP == self.helper.EOP

    def saveLog(self, request):
        with open(f"{request}Log5.txt", "w") as logFile:
            logFile.write(self.log)

    ##############################
    ####### Client Methods #######
    ##############################

    def clientRun(self, sensorID, serverID, message, dataID):
        self.com.enable()
        self.log += "Cliente:"        
        self.sensorIDNum = sensorID
        self.serverIDNum = serverID
        self.dataID = dataID
        self.messages[(dataID)], self.numPkgs = self.helper.assembleDataPackets(message, self.sensorIDNum, self.serverIDNum)
        serverAlive = False
        print("(Client) Iniciando protocolo de Handshake")
        t1_reenvio = time.perf_counter()
        t2_reenvio = time.perf_counter()
        while not serverAlive and (t2_reenvio - t1_reenvio) < 20:
            t1_timeout = time.perf_counter()
            t2_timeout = time.perf_counter()
            self.com.sendData(self.helper.createHandshake(self.sensorIDNum, self.serverIDNum, self.numPkgs, self.dataID))
            self.log += f"\n{datetime.datetime.now()} / envio / 1 / 14"
            while not serverAlive and (t2_timeout - t1_timeout) < 5:
                if self.com.rx.getBufferLen()>=14:
                    answer = self.com.rx.getBuffer(10)
                    EOP = self.com.rx.getBuffer(4)
                    serverAlive = self.checkHandshakeAnswer(answer, EOP)
                t2_timeout = time.perf_counter()
            self.com.rx.clearBuffer()
            t2_reenvio = time.perf_counter()
            if not serverAlive:
                print("(Client) O servidor ainda nao respondeu, tentando novamente")
        if not serverAlive:
            print("(Client) O servidor não respondeu, encerrando comunicação")
            self.killClient()
            return
        else:
            print("(Client) Handshake bem sucedido")

        print("(Client) Protocolo de Handshake finalizado")
        if serverAlive:
            print(f"(Client) Iniciando transmissao de {len(self.messages[(dataID)].values())} pacotes")
            startTime = time.process_time()
            finalAnswer = self.sendMessage(self.dataID)
            endTime = time.process_time()

            if finalAnswer == 1:
                print("(Client) Transmission concluded in {:.02f}s".format(endTime - startTime))
                print(f"(Client) Approximated speed: {(len(message)*(1/1000))/(endTime - startTime):.05f}kbps")

    def killClient(self):
        self.com.disable()

    def sendMessage(self, dataID):
        message = self.messages[(dataID)]
        tentativas = 0
        while self.contador <= len(message.keys()):
            verif, correcao = self.sendDatagram(message[(self.contador)])
            if verif == 0:
                print("(Client) Servidor nao respondeu, encerrando comunicacao.")
                self.killClient()
                return 0
            elif verif == 4:
                print("(Client) Servidor recebeu o pacote corretamente, preparando próximo envio.")
                self.contador += 1
            elif verif == 5:
                print("(Client) Servidor indicou time out. Encerrando comunicacao.")
                self.killClient()
                return 0
            elif verif == 6:
                print("(Client) Servidor indicou erro no pacote, enviando novamente.")
                self.contador = correcao
            else:
                print("(Client) Servidou enviou resposta inesperada, mas a transmissão será continuada normalmente.")
                self.contador += 1
        return 1

    def sendDatagram(self, datagram):
        pkgAnswer = 0
        correcao = 0
        resendPkg = None
        t1_reenvio = time.perf_counter()
        t2_reenvio = time.perf_counter()
        print(f"(Client) Contador: {self.contador}")
        while pkgAnswer == 0 and (t2_reenvio - t1_reenvio) < 20:
            t1_timeout = time.perf_counter()
            t2_timeout = time.perf_counter()
            ruido = (255).to_bytes(1, "little")
            mess = datagram
            # if random.randint(1, 100)>70:
            #     print(f"(Client) Ruído introduzido no pacote {self.contador} ---> {255}")
            #     mess = datagram[0:4] + (255).to_bytes(1, "little") + datagram[5:]
            #     self.log += f"\n{datetime.datetime.now()} / envio / 3 / {len(datagram)} / {self.contador} / {255} / {datagram[8:10].hex()}"
            # else:
            #     self.log += f"\n{datetime.datetime.now()} / envio / 3 / {len(datagram)} / {self.contador} / {datagram[3]} / {datagram[8:10].hex()}"

            self.com.sendData(mess)
            self.log += f"\n{datetime.datetime.now()} / envio / 3 / {len(datagram)} / {self.contador} / {datagram[3]} / {datagram[8:10].hex()}"
            
            print("(Client) Esperando resposta do pacote")
            while (t2_timeout - t1_timeout) < 5 and pkgAnswer == 0:
                if self.com.rx.getBufferLen()>=10:
                    answer = self.com.rx.getBuffer(10)
                    EOP = self.com.rx.getBuffer(4)
                    pkgAnswer, correcao = self.checkPackageAnswer(answer, EOP)
                t2_timeout = time.perf_counter()
            self.com.rx.clearBuffer()
            t2_reenvio = time.perf_counter()
        print(f"(Client) Tipo de resposta: {pkgAnswer}")
        return pkgAnswer, correcao

    def checkHandshakeAnswer(self, answer, EOP):
        msgType, sensorID, serverID, totalPkgs, pkgNum, dataID, resendPkg, lastSuccPkg, crc = self.helper.checkHeader(answer)
        self.log += f"\n{datetime.datetime.now()} / receb / {msgType} / 14"
        if self.checkEOP(EOP):
            if msgType == 2 and sensorID == self.sensorIDNum and serverID == self.serverIDNum:
                return 1
        return 0
    
    def checkPackageAnswer(self, answer, EOP):
        msgType, sensorID, serverID, totalPkgs, pkgNum, dataID, resendPkg, lastSuccPkg, crc = self.helper.checkHeader(answer)
        self.log += f"\n{datetime.datetime.now()} / receb / {msgType} / 14"
        if self.checkEOP(EOP):
            if sensorID == self.sensorIDNum and serverID == self.serverIDNum:
                if msgType == 4:
                    return 4, lastSuccPkg
                elif msgType == 5:
                    return 5, None
                elif msgType == 6:
                    return 6, resendPkg
        return 0, None

    ##############################
    ####### Server Methods #######
    ##############################

    def serverRun(self, saveFile, serverID):
        self.com.enable()
        self.log += "Server"
        self.saveFile = saveFile
        self.serverIDNum = serverID
        self.threadActive = True
        self.running = True
        self.thread = threading.Thread(target = self.threadJob, args=())
        self.thread.start()

    def threadJob(self):
        # noHandshakeAnswerTest = 0
        while self.running:
            if self.threadActive:    
                if self.com.rx.getBufferLen() >= 10 and self.ocioso:
                    print("(Server) Cliente mandou uma mensagem.")
                    header = self.com.rx.getBuffer(10)
                    msgType, sensorID, serverID, totalPkgs, pkgNum, dataID, resendPkg, lastSuccPkg, crc = self.helper.checkHeader(header)
                    self.handshakeCheck = 1
                if not self.running:
                    break
                if self.handshakeCheck:
                    if self.ocioso:
                        if msgType == 1 and serverID == self.serverIDNum:
                            # noHandshakeAnswerTest += 1
                            # if noHandshakeAnswerTest>4:
                            # print(noHandshakeAnswerTest)
                            self.ocioso = False
                            self.sensorIDNum = sensorID
                            self.dataID = dataID
                            self.numPkgs = totalPkgs
                            self.messages[(self.dataID)] = {}
                            print("(Server) A mensagem do cliente era um handshake")
                        time.sleep(1)
                        self.com.rx.clearBuffer()
                    else:
                        self.reply(self.helper.createHandshakeAnswer(self.sensorIDNum, self.serverIDNum), 2)
                        print("(Server) Enviando resposta do handshake")
                        self.contador = 1
                        while self.contador<=self.numPkgs and self.clientAlive:
                            isMessage = 0
                            t1_reenvio = time.perf_counter()
                            t2_reenvio = time.perf_counter()
                            while not isMessage and (t2_reenvio - t1_reenvio) < 20 and self.clientAlive:
                                t1_timeout = time.perf_counter()
                                t2_timeout = time.perf_counter()
                                while (t2_timeout - t1_timeout) < 2 and not isMessage:
                                    print("(Server) Procurando mensagens")
                                    if self.com.rx.getBufferLen()>=10:
                                        isMessage = 1
                                        print("(Server) Mensagem recebida")
                                        header = self.com.rx.getBuffer(10)
                                        msgType, sensorID, serverID, totalPkgs, pkgNum, dataID, resendPkg, lastSuccPkg, crc = self.helper.checkHeader(header)
                                        if msgType == 3:
                                            print("(Server) Cliente enviou uma mensagem do tipo 3")
                                            if self.contador == pkgNum:
                                                print("(Server) O numero do pacote é o correto")
                                                if self.com.rx.getBufferLen() >= dataID:
                                                    payload = self.com.rx.getBuffer(dataID)
                                                    if self.com.rx.getBufferLen() >= 4:
                                                        EOP = self.com.rx.getBuffer(4)
                                                        if self.checkCRC(crc, payload):
                                                            if self.checkEOP(EOP):
                                                                print("(Server) O pacote esta correto")
                                                                print(f"(Server) Contador: {self.contador}")
                                                                self.log += f"\n{datetime.datetime.now()} / receb / {msgType} / {dataID + 14} / {pkgNum} / {totalPkgs} / {crc.hex()}"
                                                                self.reply(self.helper.createPackageAnswer(self.sensorIDNum, self.serverIDNum, self.contador), 4)
                                                                self.contador += 1
                                                                # self.lastSuccPkg = pkgNum
                                                                self.messages[(self.dataID)][(pkgNum)] = payload
                                                            else:
                                                                self.log += f"\n{datetime.datetime.now()} / receb / {msgType} / {dataID + 14} / {pkgNum} / {totalPkgs} / {crc.hex()}"                                                                
                                                                print("(Server) Pelo menos um erro foi encontrado no EOP. Pedindo reenvio")
                                                                self.reply(self.helper.createErrorMsg(self.sensorIDNum, self.serverIDNum, self.contador), 6)
                                                                self.com.rx.clearBuffer()
                                                        else:
                                                            self.log += f"\n{datetime.datetime.now()} / receb / {msgType} / {dataID + 14} / {pkgNum} / {totalPkgs} / {crc.hex()}"
                                                            print("(Server) Pelo menos um erro foi encontrado no payload. Pedindo reenvio")
                                                            self.reply(self.helper.createErrorMsg(self.sensorIDNum, self.serverIDNum, self.contador), 6)
                                                            self.com.rx.clearBuffer()
                                                    else:
                                                        self.log += f"\n{datetime.datetime.now()} / receb / {msgType} / {dataID + 14} / {pkgNum} / {totalPkgs} / {crc.hex()}"
                                                        print("(Server) Pelo menos um erro foi encontrado no payload (Check de tamanho para pegar EOP). Pedindo reenvio")
                                                        self.reply(self.helper.createErrorMsg(self.sensorIDNum, self.serverIDNum, self.contador), 6)
                                                        self.com.rx.clearBuffer()
                                                else:
                                                    self.log += f"\n{datetime.datetime.now()} / receb / {msgType} / {dataID + 14} / {pkgNum} / {totalPkgs} / {crc.hex()}"
                                                    print("(Server) Pelo menos um erro foi encontrado no pacote (Check de tamanho do payload). Pedindo reenvio")
                                                    self.reply(self.helper.createErrorMsg(self.sensorIDNum, self.serverIDNum, self.contador), 6)
                                                    self.com.rx.clearBuffer()
                                            else:
                                                self.log += f"\n{datetime.datetime.now()} / receb / {msgType} / {dataID + 14} / {pkgNum} / {totalPkgs} / {crc.hex()}"
                                                print("(Server) Pelo menos um erro foi encontrado no pacote (Erro no contador). Pedindo reenvio")
                                                self.reply(self.helper.createErrorMsg(self.sensorIDNum, self.serverIDNum, self.contador), 6)
                                                self.com.rx.clearBuffer()
                                        else:
                                            self.log += f"\n{datetime.datetime.now()} / receb / {msgType} / {dataID + 14} / {pkgNum} / {totalPkgs} / {crc.hex()}"
                                            print("(Server) Pelo menos um erro foi encontrado no pacote (Nao é tipo 3). Pedindo reenvio")
                                            self.reply(self.helper.createErrorMsg(self.sensorIDNum, self.serverIDNum, self.contador), 6)
                                            self.com.rx.clearBuffer()
                                    else:
                                        time.sleep(1)
                                    t2_timeout = time.perf_counter()
                                if not isMessage:
                                    print("(Server) Pacote não foi recebido, mas mensagem tipo 4 foi enviada")
                                    self.reply(self.helper.createPackageAnswer(self.sensorIDNum, self.serverIDNum, self.contador), 4)
                                t2_reenvio = time.perf_counter()
                            if not isMessage:
                                self.ocioso = True
                                print("(Server) O cliente demorou para enviar o pacote, encerrando comunicação")
                                self.reply(self.helper.createTimeoutMsg(self.sensorIDNum, self.serverIDNum), 5)
                                self.clientAlive = False
                                self.killServer()
                        if len(self.messages[(self.dataID)]) == 0:
                            print("(Server) Cliente apenas disse 'Oi'")
                        elif len(self.messages[(self.dataID)])>0:
                            print("(Server) Arquivo recebido foi salvo")
                            self.saveImage(self.dataID)
                        self.killServer()
                    time.sleep(1)

    
    def saveImage(self, dataID):
        sentData = self.messages[self.dataID].values()
        saida = b"".join(sentData)
        with open(self.saveFile, "wb") as outFile:
            outFile.write(saida)
    
    def killServer(self):
        self.running = False
        self.threadActive = False
        self.com.disable()
   
    def checkCRC(self, crc, payload):
        crc16_func = crcmod.mkCrcFun(0x11021, initCrc=0, xorOut=0xFFFFFFFF)
        crc_check = crc16_func(payload).to_bytes(2, "little")
        return crc == crc_check
        
    def reply(self, message, msgType):
        self.com.sendData(message)
        print(f"(Server) resend/lastSuccPkg {message[6]}, {message[7]}")
        self.log += f"\n{datetime.datetime.now()} / envio / {msgType} / 14"