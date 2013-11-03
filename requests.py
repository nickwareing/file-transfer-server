from struct import *

def open_request(filename='', structure = 'H', open_req = 33):
    packet = pack(structure, open_req) + filename
    return packet


def read_request(handle_number=0, epoch_number=0, start_position=0, num_bytes=0, structure_A = 'HHH', structure_B = 'II', read_req=55):
    partA = pack(structure_A, read_req, handle_number, epoch_number)
    partB = pack(structure_B, start_position, num_bytes)
    packet = partA + partB
    return packet


def close_request(handle_number=0, structure='HH', close_req=77):
	packet = pack(structure, close_req, handle_number)
	return packet
