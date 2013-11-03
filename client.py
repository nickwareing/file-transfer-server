import os.path
import socket
import time
import select

from transfer import *
from requests import *
from measurments import *

class ClientFileTransferSocket(object):
    
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #Create a socket object
        self.remoteFileName = self.getRemoteFileName()
        self.localFileName = self.getLocalFileName()
        self.port = self.getPort()
        self.serverIP = self.getserverIP()
        self.dropProbability = getDropProbability()
        self.handle_number = 0
        self.data_buffer = []
        self.exitFlag = 0
        self.expectedStartPosition = 0
        
    def getLocalFileName(self):
        inputNotValid = True
        filename = raw_input("Enter the filename under which the recieved file should be stored: ")
        while inputNotValid:
            if not os.path.exists(filename):
                inputNotValid = False
                continue
            filename = raw_input("That file already exists, please enter another: ")
        return filename
        
    def getRemoteFileName(self):
        return raw_input("Enter the filename to be read: ")
        
    def getserverIP(self):
        return raw_input("Enter the IP address of the file server: ")
        
    def getPort(self):
        try:
            port = raw_input("Enter the server port number: ")
            while (float(port) % 1 != 0 or float(port) > 10000 or float(port) < 0):
                port = raw_input("That wasn't valid, please try again: ")
        except ValueError, e:
            print "That input was invalid, exiting now."
            exit()
        return int(port)
        
    #Writes data to a file, using the append mode, so that it can
    #be called multiple times, for different chunks.    
    def storeFile(self, msg):
        outputFile = open(self.localFileName, 'a')
        outputFile.write(msg)
        outputFile.close()
    
    #Sends an open request containting the name of the file to be
    #retrieved.
    def requestFile(self):
        self.s.sendto(open_request(self.remoteFileName), (self.serverIP, self.port))
        self.fillBuffer()
    
    #Receives a packet and puts it in a buffer.    
    def fillBuffer(self):
        while self.exitFlag == 0: 
			#Check whether there are packets at the socket.
			#Timeout after 5 seconds if there are no packets.
            ready = select.select([self.s], [], [], 1)
            #Only enter the blocking recv call if there is a packet at the socket.
            if ready[0]:
                packet, addr = self.s.recvfrom(CHUNK_SIZE + MAX_HEADER_SIZE)
                self.data_buffer = []
                for i in packet:
                    self.data_buffer.append(i)
            self.readBuffer()
        
    
    #Checks the type of a packet, and then acts accordingly.    
    def readBuffer(self):
        if (dropOrKeepPacket(self.dropProbability) == True):
			print "Dropped packet (client)."
			return
            
        elif (len(self.data_buffer) == 0):
            self.s.sendto(read_request(self.handle_number, 0, self.expectedStartPosition, CHUNK_SIZE), (self.serverIP, self.port))
            return
            
        packetContents = packet_type(self.data_buffer)
        
        if packetContents[0] == OPEN_RESPONSE:
            status = packetContents[1][0]
            if status == 1:
                print "Got a positive open response from %s, sending read request now." % self.serverIP
                self.handle_number = packetContents[1][2]
                epoch_number = packetContents[1][1]
                num_bytes = CHUNK_SIZE
                self.s.sendto(read_request(self.handle_number, epoch_number, self.expectedStartPosition, num_bytes), (self.serverIP, self.port))
            elif status == 0:
				print "The server doesn't have that file, exiting now."
				self.exitFlag = 1 
            
        elif packetContents[0] == READ_RESPONSE:
            print "Got a read response from %s, postion %s, storing chunk now." % (self.serverIP, packetContents[1][4])
            self.storeFile(packetContents[1][-1])
            self.handle_number = packetContents[1][1]
            epoch_number = packetContents[1][2]
            if (packetContents[1][0]) == 3:
                print "Sending close request now."
                self.s.sendto(close_request(self.handle_number), (self.serverIP, self.port))
            elif (packetContents[1][4] == self.expectedStartPosition):
                #Ask for the next block only if the block we just got was the one we wanted. 
                self.expectedStartPosition += CHUNK_SIZE
                self.s.sendto(read_request(self.handle_number, epoch_number, self.expectedStartPosition, CHUNK_SIZE), (self.serverIP, self.port))
            else:
				#Otherwise ask for the old one again.
                self.s.sendto(read_request(self.handle_number, epoch_number, self.expectedStartPosition, CHUNK_SIZE), (self.serverIP, self.port))

        elif packetContents[0] == CLOSE_RESPONSE:
            print "Close Confirmed."
            self.exitFlag = 1
        
        else:
            print "Incoming packet is invalid."
   
client = ClientFileTransferSocket()
try:        
    client.requestFile()
except socket.error, e:
    print "A socket error occured, maybe the IP address you provided isn't correct."
    print "Exiting now"
