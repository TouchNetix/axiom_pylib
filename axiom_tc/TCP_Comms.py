# Copyright (c) 2025 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import socket

class TCP_Comms:
    wMaxPacketSize = 255
    AX_TBP_I2C_DEV_HEAD_LEN = 3
    AX_HEADER_LEN = 0x4

    CMD_AXIOM_COMMS      = 0x51
    CMD_MULTIPAGE_READ   = 0x71
    CMD_START_PROXY_MODE = 0x88
    CMD_EXIT             = 0xFF

    STATUS_READ_WRITE_OK            = 0x00
    STATUS_DEVICE_COMMS_FAILED      = 0x01
    STATUS_DEVICE_TIMEOUT           = 0x02
    STATUS_WRITE_OK_NO_READ_REQUEST = 0x04
    STATUS_INVALID_REQUEST          = 0xFF

    def __init__(self, host, port=3825):
        self._host = host
        self._port = port

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self._host, self._port))

        self._axiom = None

    def comms_init(self, axiom):
        self._axiom = axiom

    def read_page(self, target_address, length):
        data = []
        remaining_length = length
        current_address = target_address

        while remaining_length > 0:
            chunk_length = min(remaining_length, self.wMaxPacketSize)

            ta_msb = (current_address & 0xFF00) >> 8
            ta_lsb = (current_address & 0x00FF)

            length_msb = (chunk_length & 0x7F00) >> 8
            length_lsb = (chunk_length & 0x00FF)

            length_msb |= 0x80  # Set the READ bit

            message = bytes([self.CMD_AXIOM_COMMS, 4, chunk_length] + [ta_lsb, ta_msb, length_lsb, length_msb])
            self._sock.sendall(message)
            response = self._sock.recv(chunk_length + 1)  # Receive chunk_length + 1 bytes (status + data)

            data.extend(response[1:])  # Skip the first byte which is the status

            remaining_length -= chunk_length
            current_address += chunk_length  # Increment the address for the next chunk
        return data

    def write_page(self, target_address, length, payload):
        remaining_length = length
        current_address = target_address
        payload_offset = 0

        while remaining_length > 0:
            chunk_length = min(remaining_length, self.wMaxPacketSize)
            chunk_payload = payload[payload_offset:payload_offset + chunk_length]

            ta_msb = (current_address & 0xFF00) >> 8
            ta_lsb = (current_address & 0x00FF)

            length_msb = (chunk_length & 0x7F00) >> 8
            length_lsb = (chunk_length & 0x00FF)

            message = bytes([self.CMD_AXIOM_COMMS, 4 + chunk_length, 0] + [ta_lsb, ta_msb, length_lsb, length_msb] + chunk_payload)
            self._sock.sendall(message)
            _ = self._sock.recv(1)  # Receive acknowledgment (1 byte)

            remaining_length -= chunk_length
            current_address += chunk_length  # Increment the address for the next chunk
            payload_offset += chunk_length  # Move the payload offset forward
        return
    
    def close(self):
        self._sock.sendall(bytes([self.CMD_EXIT]))
        self._sock.close()
