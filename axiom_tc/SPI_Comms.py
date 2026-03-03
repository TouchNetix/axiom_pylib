# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import logging
from time import sleep
import spidev
import sys

logger = logging.getLogger(__name__)

class SPI_Comms:
    COMMS_TYPE = "SPI"
    SPI_PADDING_LEN = 32
    AX_HEADER_LEN = 4

    def __init__(self, bus, device):
        self._spi = spidev.SpiDev()
        self._spi.open(bus, device)

        # Configure SPI bus, less than 7MHz will work
        self._spi.max_speed_hz = 7000000
        self._spi.mode = 0

        self.detect_device()

    def comms_init(self):
        return

    def detect_device(self):
        # We read a small amount of data to see if the MISO line is alive
        # A 4-byte read results in a 40-byte total SPI transfer
        data = self.read_page(0x0000, 4)
        
        # Check if the data is just floating (all 1s or all 0s)
        if all(b == 0xFF for b in data) or all(b == 0x00 for b in data):
            logger.error("aXiom not detected on SPI. MISO line is floating or pulled.")
            sys.exit(1)
        
        return True
    
    def read_page(self, target_address, length, ignore_return = False):
        ta_msb = (target_address & 0xFF00) >> 8
        ta_lsb = (target_address & 0x00FF)

        length_msb = (length & 0x7F00) >> 8
        length_lsb = (length & 0x00FF)

        length_msb |= 0x80  # Set the READ bit

        # Pre-allocate operation buffer
        spi_op = bytearray(self.AX_HEADER_LEN + self.SPI_PADDING_LEN + length)
        
        # Fill the header
        spi_op[0] = ta_lsb
        spi_op[1] = ta_msb
        spi_op[2] = length_lsb
        spi_op[3] = length_msb

        spi_op[self.AX_HEADER_LEN + self.SPI_PADDING_LEN] = 1
        
        rx_data = self._spi.xfer(spi_op)
        
        sleep(0.01) # transaction errors happen without a delay 

        return bytearray(rx_data[self.AX_HEADER_LEN + self.SPI_PADDING_LEN:])

    def write_page(self, target_address, length, payload: bytearray, ignore_return = False, bl_sync = False):
        if length > len(payload):
            logger.error(f"Write overflow: length {length}, payload {len(payload)}")
            raise AssertionError

        ta_msb = (target_address & 0xFF00) >> 8
        ta_lsb = (target_address & 0x00FF)

        length_msb = (length & 0x7F00) >> 8
        length_lsb = (length & 0x00FF)

        length_msb &= ~0x80  # Ensure the read bit is clear

        spi_header = bytearray([ta_lsb, ta_msb, length_lsb, length_msb])
        spi_padding = bytearray(32) # Creates 32 null bytes
        
        spi_op = spi_header + spi_padding + payload[:length]

        if bl_sync:
            # If accumulating data in the bootloader, add an empty sync payload.
            spi_op += bytearray(80)

        self._spi.xfer(spi_op)

        sleep(0.01) # transaction errors happen without a delay 

    def close(self, u34_address, max_report_len):
        self._spi.close()
