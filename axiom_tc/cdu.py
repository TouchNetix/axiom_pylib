# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import time


CDU_CMD_FETCH = 0x0001
CDU_CMD_STORE = 0x0002
CDU_CMD_COMMIT = 0x0003
CDU_CMD_QUERY = 0x0004

CDU_ERROR_MASK = 0x8000

CDU_HEADER_LEN = 8
CDU_PAYLOAD_LEN = 48
CDU_LEN = CDU_HEADER_LEN + CDU_PAYLOAD_LEN

TIMEOUT = 5

def read(comms, address, length):
    return fetch(comms, address, length)

def write(comms, address, buffer):
    store(comms, address, buffer)

def send_cmd(comms, address: int, cmd_code: int, arg1: int, arg2: int, arg3: int, response_len: int, payload=None):

    assert response_len >= CDU_HEADER_LEN and response_len <= CDU_LEN

    buffer = bytearray(CDU_HEADER_LEN)
    
    buffer[0:2] = cmd_code.to_bytes(2, 'little')
    buffer[2:4] = arg1.to_bytes(2, 'little')
    buffer[4:6] = arg2.to_bytes(2, 'little')
    buffer[6:8] = arg3.to_bytes(2, 'little')

    if payload:
        assert len(payload) <= CDU_PAYLOAD_LEN
        buffer.extend(payload)

    comms.write_page(address, len(buffer), buffer)
    
    # The commit command has no response when it succeeds, return immediately.
    if cmd_code == CDU_CMD_COMMIT:
        return bytearray()
    
    start_time = time.time()
    while (time.time() - start_time) < TIMEOUT:
        # time.sleep(0.1)

        response_buffer = comms.read_page(address, response_len)

        status = int.from_bytes(response_buffer[0:2], 'little')

        # the device is still busy
        if status == cmd_code:
            continue
        
        if status == 0:
            return response_buffer

        if (status & CDU_ERROR_MASK):
            raise AssertionError(f"CDU Command {hex(cmd_code)} failed with status {hex(status)}")
    else:
        raise AssertionError("CDU Command timed out")
    
def query(comms, address, usage):

    # We're only interested in the header plus first byte of the payload.
    response_len = CDU_HEADER_LEN + 1

    result = send_cmd(comms, address, CDU_CMD_QUERY, 0, 0, 0, response_len=response_len)

    param0 = int.from_bytes(result[2:4], 'little')
    param1 = int.from_bytes(result[4:6], 'little')
    param2 = int.from_bytes(result[6:8], 'little')

    # uifrevision = int.from_bytes(result[8:10], 'little')

    # Length in bytes is param0 * param1, param 2 is not used
    # Unfortunately, u93 is still a special case - this should be
    # addressed in the future
    if usage != 0x93:
        cdu_usage_length = param0 * param1
    else:
        cdu_usage_length = param1 * param2
 
    return cdu_usage_length

def fetch(comms, address, length):

    result_buffer = bytearray(length)
    offset = 0

    while offset < length:
        remaining = length - offset
        chunk_len = min(remaining, CDU_PAYLOAD_LEN)

        response = send_cmd(comms, address, CDU_CMD_FETCH, offset, 0, 0, chunk_len)
        
        # Extract payload
        data = response[CDU_HEADER_LEN:]
        
        result_buffer[offset : offset + chunk_len] = data[:chunk_len]

        offset += CDU_PAYLOAD_LEN

    return result_buffer

def store(comms, address, buffer):
    offset = 0
    total_len = len(buffer)
    
    while offset < total_len:
        # Prepare the chunk for the payload
        chunk = buffer[offset : offset + CDU_PAYLOAD_LEN]

        send_cmd(comms, address, CDU_CMD_STORE, 0, offset, 0, CDU_HEADER_LEN, payload=chunk)
        
        offset += CDU_PAYLOAD_LEN

def commit(comms, address):
    send_cmd(comms, address, CDU_CMD_COMMIT, 0xB10C, 0xC0DE, 0, CDU_HEADER_LEN)
    time.sleep(1)
