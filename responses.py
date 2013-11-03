from struct import *

def open_response(status=0, epoch_number=0, file_length=0, handle_number=0, structure_A = 'HHHH', structure_B = 'I', open_res=44):
    partA = pack(structure_A, open_res, status, epoch_number, handle_number)
    partB = pack(structure_B, file_length)
    packet = partA + partB
    return packet
        
        
def read_response(handle_number=0, epoch_number=0, start_position=0, num_bytes=0, status=0, data='', structure_A = 'HHHH', structure_B = 'II', read_res=66):
    partA = pack(structure_A, read_res, status, handle_number, epoch_number)
    partB = pack(structure_B, num_bytes, start_position)
    packet = partA + partB + data
    return packet


def close_response(handle_number=0, structure='HH', close_res=88):
	packet = pack(structure, close_res, handle_number)
	return packet
