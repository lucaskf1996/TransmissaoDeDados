import os
import crcmod

class Helper:
    def __init__(self):
        self.storage = {}
        self.EOP = bytes([255,170,255,170])

    def getStorage(self):
        return self.storage
    
    def retrieveFromStorage(self, key):
        try:
            return self.storage
        except KeyError as e:
            print("Key not found", e)
            return

    def constructParcel(self, head = None, data = None):      
        if head != None:
            message = head
        if data != None:
            message += data
        if self.EOP != None:
            message += self.EOP
        return message

    def buildPaths(self, data):
        "data == filepath"
        selectedFile = data
        selectedFileExtension = os.path.splitext(selectedFile)[1]
        saveFileLocation = os.path.splitext(selectedFile)[0] + "Received" + selectedFileExtension
        return selectedFile, saveFileLocation

    def breakData(self, data):
        packetAmount = len(data)//114 + 1
        
        allData = [[] for i in range(packetAmount)]
        content = data[:]
        for i in range(packetAmount):
            if i<packetAmount-1:
                allData[i] = content[0:114]
                content = content[114:]
            else:
                allData[i] = content[:]            

        return allData, packetAmount

    def checkHeader(self, header):
        # print(header)
        # print(header[0])
        msgType     = header[0] #int.from_bytes(header[0], "little") 
        sensorID    = header[1] #int.from_bytes(header[1], "little")
        serverID    = header[2] #int.from_bytes(header[2], "little")
        totalPkgs   = header[3] #int.from_bytes(header[3], "little")
        pkgNum      = header[4] #int.from_bytes(header[4], "little")
        dataID      = header[5] #int.from_bytes(header[5], "little")
        resendPkg   = header[6] #int.from_bytes(header[6], "little")
        lastSuccPkg = header[7] #int.from_bytes(header[7], "little")
        crc         = header[8:10] #int.from_bytes(header[8:10], "little")

        return(msgType, sensorID, serverID, totalPkgs, pkgNum, dataID, resendPkg, lastSuccPkg, crc)

    def assembleDataPackets(self, data, sensorID, serverID):
        crc16_func = crcmod.mkCrcFun(0x11021, initCrc=0, xorOut=0xFFFFFFFF)
        out = {}
        content, totalPkgs = self.breakData(data)
        for i, e in enumerate(content):
            crc_out = crc16_func(e).to_bytes(2, "little")
            header = bytes([3, sensorID, serverID, totalPkgs, (i+1), len(e), 0, 0])
            header += crc_out
            out[(i+1)] = self.constructParcel(head = header, data = e)
        return out, totalPkgs
    
    def createHandshake(self, sensorID, serverID, totalPkgs, dataID):
        return self.constructParcel(head = bytes([1, sensorID, serverID, totalPkgs, 0, dataID, 0, 0, 0, 0]))
    
    def createHandshakeAnswer(self, sensorID, serverID):
        return self.constructParcel(head = bytes([2, sensorID, serverID, 0, 0, 0, 0, 0, 0, 0]))

    def createErrorMsg(self, sensorID, serverID, resendPkg):
        return self.constructParcel(head = bytes([6, sensorID, serverID, 0, 0, 0, resendPkg, 0, 0, 0]))

    def createTimeoutMsg(self, sensorID, serverID):
        return self.constructParcel(head = bytes([5, sensorID, serverID, 0, 0, 0, 0, 0, 0, 0]))

    def createPackageAnswer(self, sensorID, serverID, lastSuccPkg):
        return self.constructParcel(head = bytes([4, sensorID, serverID, 0, 0, 0, 0, lastSuccPkg, 0, 0]))