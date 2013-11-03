from struct import *

OPEN_REQUEST = 33
OPEN_RESPONSE = 44
READ_REQUEST = 55
READ_RESPONSE = 66
CLOSE_REQUEST = 77
CLOSE_RESPONSE = 88

MAX_HEADER_SIZE = 176 #IP + UDP + read_response headers. 
CHUNK_SIZE = 1324 #Ethernet upper bound (1500 bytes) minus MAX_HEADER_SIZE.


#Reads each 16 bit (2 byte) packet field individually. 
def read_2bytes(data_buffer):
	byte1 = ord(data_buffer.pop(0))
	byte2 = ord(data_buffer.pop(0))
	data = byte1 + (byte2 * 256)

	return data


#Reads a 32 bit (4 byte) packet field.    
def read_4bytes(data_buffer):
	byte1 = ord(data_buffer.pop(0))
	byte2 = ord(data_buffer.pop(0))
	byte3 = ord(data_buffer.pop(0))
	byte4 = ord(data_buffer.pop(0))
	data = byte1 + (byte2 * 256) + (byte3 * 256**2) + (byte4 * 256**3)

	return data


#Reads the rest of an open request packet, returning the filename.
def open_request(data_buffer):
	filename = ''
	while data_buffer != []:
		filename += data_buffer.pop(0)

	return filename


#Reads in the remaining fields for an open response packet.
def open_response(data_buffer):
	i = 0
	info = []
	while data_buffer != []:
		if i <= 2:
			info.append(read_2bytes(data_buffer))
		else:
			info.append(read_4bytes(data_buffer))
		i += 1

	return info #This includes the status, file_length and file_handle fields.


#Reads in the remaining fields for an read request packet.
def read_request(data_buffer):
	i = 0
	info = []
	while data_buffer != []:
		if i < 2:
			info.append(read_2bytes(data_buffer))
		else:
			info.append(read_4bytes(data_buffer))
		i += 1

	return info #This includes the file_handle, start position and number of bytes to read.


#Reads in the remaining fields for an read response packet, including a string of the downloaded file.
def read_response(data_buffer):
	i = 0
	info = []
	data = ''
	while data_buffer != []:
		if i <= 2:
			info.append(read_2bytes(data_buffer))
		elif 2 < i <= 4 :
			info.append(read_4bytes(data_buffer))
		else:
			data += data_buffer.pop(0)
		i += 1

	info.append(data)
	return info #This includes the status, file handle, start position, number of bytes and the file data itself.
	
	
def close_request(data_buffer):
	info = []
	while data_buffer != []:
		info.append(read_2bytes(data_buffer))
		
	return info
	


def packet_type(data_buffer):
	p_type = read_2bytes(data_buffer)

	if p_type == OPEN_REQUEST:
		info = open_request(data_buffer)
	elif p_type == OPEN_RESPONSE:
		info = open_response(data_buffer)
	elif p_type == READ_REQUEST:
		info = read_request(data_buffer)
	elif p_type == READ_RESPONSE:
		info = read_response(data_buffer)
	elif p_type == CLOSE_REQUEST:
		info = close_request(data_buffer)
	elif p_type == CLOSE_RESPONSE:
		info = close_request(data_buffer)
	else:
		p_type = -1
		info = "Invalid packet"

	return (p_type, info)
