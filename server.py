import os
import socket
from time import time

from transfer import *
from responses import *
from measurments import *

class ServerFileTransferSocket(object):
    
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Create a UDP socket object
        self.port = self.getPort()
        self.host = socket.gethostname() # Get local machine name
        self.dropProbability = getDropProbability()
        self.s.bind((self.host, self.port))
        self.data_buffer = []
        self.epochNumber = self.getEpochNumber()
        self.contextRecord = {}
        self.exitFlag = 0
    
    def getPort(self):
        try:
            port = raw_input("Enter a port number: ")
            while (float(port) % 1 != 0 or float(port) > 10000 or float(port) < 0):
                port = raw_input("That wasn't valid, please try again: ")
        except ValueError, e:
            print "That input was invalid, exiting now."
            exit()
        return int(port)
        
    def getEpochNumber(self):
        if os.path.exists("epoch.number"):
            epochFile = open("epoch.number", "r")
            epochNumber = int(epochFile.read(1))
            epochNumber += 1
            epochFile.close()
            epochFile = open("epoch.number", "w")
            epochFile.write(str(epochNumber))
            epochFile.close()
        else:
            epochFile = open("epoch.number", "w+")
            epochNumber = int(1)
            epochFile.write(str(epochNumber))
            epochFile.close() 
            
        return epochNumber;
        
    #Checks the timers of all context records, and deletes the records
    #if the timer has expired.    
    def checkTimers(self):
        for k, v in self.contextRecord.iteritems():
            if (v[1] < time()):
                v[0].close()
                del self.contextRecord[k]
                if (len(self.contextRecord) == 0):
                    self.exitFlag = 1
    
    #Receives a packet and puts it in a buffer.
    def fillBuffer(self):
        self.checkTimers()    
        while self.exitFlag == 0:    
            packet, addr = self.s.recvfrom(MAX_HEADER_SIZE)
            self.data_buffer = []
            for i in packet:
                self.data_buffer.append(i)
            self.readBuffer(addr)
     
    #Checks the type of a packet, and then acts accordingly.                   
    def readBuffer(self, addr):
        if (len(self.data_buffer) == 0 or dropOrKeepPacket(self.dropProbability) == True):
            print "Dropped packet (server)."
            return
            
        packetContents = packet_type(self.data_buffer)
        if packetContents[0] == OPEN_REQUEST:
            print "Got an open request from %s to open %s." % (addr, packetContents[1])
            status = os.path.exists(packetContents[1])
            #Now that transfer has started, we set the socket
            #to timeout if it is left ideal for 30seconds.
            self.s.settimeout(30)
            if status == 1:
                file_length = int(os.path.getsize(packetContents[1]))
                requestedFile = open(packetContents[1], "r")
                handle_number = requestedFile.fileno()
                #Store information regarding this clients transfer
                #in a python dictionary.
                self.contextRecord[handle_number] = [requestedFile]
                self.contextRecord[handle_number].append(time()+30)
                self.contextRecord[handle_number].append(file_length)
                self.contextRecord[handle_number].append(-1)
                self.contextRecord[handle_number].append('')
                self.s.sendto(open_response(status, self.epochNumber, file_length, handle_number), addr)
                
            elif status == 0:
                self.s.sendto(open_response(status, 0, 0, 0), addr) #If the file does not exist, send back an empty response packet.
        
        elif packetContents[0] == READ_REQUEST:
            print "Got a read request from %s, wanting %s bytes of a file." % (addr, packetContents[1][3])
            handle_number = packetContents[1][0]
            start_position = packetContents[1][2]
            epoch_number = packetContents[1][1]
            
            #Check the packet belongs to this instance of the server.
            if (epoch_number != self.epochNumber):
                status = 1
            #Checks a context record exists for this client.
            elif handle_number not in self.contextRecord:
                status = 2 
            #Check whether the complete file has already been sent.
            elif (start_position > self.contextRecord[handle_number][2]):
                status = 3
            else:
                status = 4
                self.contextRecord[handle_number][1] = time()+30 #The context for a read-request has been found, the corresponding timer is re-started with its initial timeout value.
            
            #Read the next chunk of data from the appropriate file and
            #send to client the read request came from. 
            if (status == 4):
                if (start_position != self.contextRecord[handle_number][3]):
                    handle_number = packetContents[1][0]
                    self.contextRecord[handle_number][4] = self.contextRecord[handle_number][0].read(CHUNK_SIZE)
                    self.contextRecord[handle_number][3] = start_position
                self.s.sendto(read_response(handle_number, self.epochNumber, self.contextRecord[handle_number][3], CHUNK_SIZE, status, self.contextRecord[handle_number][4]), addr)
            else:
                self.s.sendto(read_response(handle_number, self.epochNumber, self.contextRecord[handle_number][3], CHUNK_SIZE, status, ''), addr)       
            
        elif packetContents[0] == CLOSE_REQUEST:
            print "Transfer complete, closing the file and sending close response."
            handle_number = packetContents[1][0]
            self.s.sendto(close_response(handle_number), addr)
            self.contextRecord[handle_number][0].close()
            del self.contextRecord[handle_number]
            if (len(self.contextRecord) == 0):
                self.exitFlag = 1
                
        else:
            print "Incoming packet is invalid."

server = ServerFileTransferSocket()
try:
    server.fillBuffer()
except socket.error, e:
    print "A socket error or timeout occured."
    print "Exiting now"
