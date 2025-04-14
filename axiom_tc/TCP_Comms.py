# Copyright (c) 2025 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import socket
import time

class TCP_Comms:
    wMaxPacketSize = 255
    AX_TBP_I2C_DEV_HEAD_LEN = 3
    AX_HEADER_LEN = 0x4

    CMD_AXIOM_COMMS       = 0x51
    CMD_MULTI_PHASE_READ  = 0x71
    CMD_SINGLE_PHASE_READ = 0x75
    CMD_NULL              = 0x86
    CMD_START_PROXY_MODE  = 0x88
    CMD_FIND_I2C_ADDRESS  = 0xE0
    CMD_EXIT              = 0xFF

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
            response = self._sock.recv(chunk_length + 2)  # Receive chunk_length + 2 bytes (status + data)

            data.extend(response[2:])  # Skip the first 2 bytes which is the status and length

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
            _ = self._sock.recv(2)  # Receive acknowledgment (1 byte)

            remaining_length -= chunk_length
            current_address += chunk_length  # Increment the address for the next chunk
            payload_offset += chunk_length  # Move the payload offset forward
        return

    def wait_for_proxy_reports(self):
        self._sock.settimeout(2)
        try:
            response = self._sock.recv(0x3A + 2)
            print('[{}]'.format(' '.join(hex(x) for x in response)))
        except socket.timeout:
            print("No data received within the timeout period.")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self._sock.settimeout(None)

    def proxy_mode(self, enable : bool):
        if enable:
            message = bytes([self.CMD_START_PROXY_MODE, 0x00, 0x04, 0x3A, 0x00, 0x08, 0x3A, 0x80])
            self._sock.sendall(message)
            _ = self._sock.recv(2)
        else:
            message = bytes([self.CMD_NULL])
            self._sock.sendall(message)
            _ = self._sock.recv(1)
            time.sleep(0.1)

    def large_read(self, target_address, length):
        rx_len_lsb = (length & 0x00FF)
        rx_len_msb = (length & 0xFF00) >> 8

        ta_lsb = (target_address & 0x00FF)
        ta_msb = (target_address & 0xFF00) >> 8

        message = bytes([self.CMD_MULTI_PHASE_READ, 4, rx_len_lsb, rx_len_msb, 0, ta_lsb, ta_msb])
        self._sock.sendall(message)
        response = self._sock.recv(length + 2)
        #print('[{}]'.format(' '.join(hex(x) for x in response)))
        print("|", end=' ') 
        for x in range(2, length, 2):
            value = response[x] & 0xFF | (response[x+1] << 8)
            if value & 0x8000:  # Check if the MSB is set
                value -= 0x10000  # Adjust to signed value

            value = -value

            # Choose a Braille character based on the value
            if value < 500:
                char = ' '  # Very small values
            elif value < 1000:
                char = '.'  # Small values
            elif value < 2000:
                char = '*'  # Medium values
            elif value < 3000:
                char = '#'  # Large values
            else:
                char = '@'  # Very large values

            print(char, end='')  # Print the Braille character without a newline
        print("|")

    def find_i2c_address(self):
        message = bytes([self.CMD_FIND_I2C_ADDRESS])
        self._sock.sendall(message)
        response = self._sock.recv(2)
        print('[{}]'.format(' '.join(hex(x) for x in response)))
    
    def close(self):
        self._sock.sendall(bytes([self.CMD_EXIT]))
        self._sock.close()
