# Notes for data packet

The following structure is to be adopted for a data packet:

- It's size is to be no more than 128 bytes
- The first 10 bytes are to be it's header
- The next 0 to 114 bytes are it's message
- The final 4 bytes are the EOP (end of packet), which can be any value.

In the 10 bytes that constitute the header, one must specify all required information for the server to process and store the information sent.
 
1.       msgType
2.       sensorID
3.       serverID
4.       totalPkgs
5.       pkgNum
6.       dataID if handshake
         payloadSize if msgType 3
7.       resendPkg
8.       lastSuccPkg
9. - 10. CRC


to do:
