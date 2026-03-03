# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from smbus2 import SMBus, i2c_msg
import time
import logging
import errno
import sys

logger = logging.getLogger(__name__)

class I2C_Comms:
    COMMS_TYPE = "I2C"

    def __init__(self, bus, address):
        self._addr = address
        self._bus = SMBus(bus)

        self.detect_device()
        
    def comms_init(self):
        return
    
    def detect_device(self):
        """
        Checks for the presence of a device at a specific address.
        Returns True if the device ACKs, False otherwise.
        """
        try:
            # write_quick(address) sends only the address byte with the write bit.
            self._bus.write_quick(self._addr)
            return True
        except OSError as e:
            if e.errno == errno.EREMOTEIO: # Error 121 is 'Remote I/O error' (No ACK)
                logger.error(f"Did not find aXiom at address 0x{self._addr:02x}.")
                sys.exit(1)
            elif e.errno == errno.EBUSY: # Error 16 is 'Device or resource busy' (Already in use by a driver)
                logger.warning("aXiom is already in use.")
                return True
            else:
                raise

    def read_page(self, target_address, length, ignore_return = False):
        
        header = bytearray(4)
        header[0] = target_address & 0x00FF         # ta_lsb
        header[1] = (target_address & 0xFF00) >> 8  # ta_msb
        header[2] = length & 0x00FF                 # length_lsb
        header[3] = ((length & 0x7F00) >> 8) | 0x80 # length_msb + READ bit

        wr = i2c_msg.write(self._addr, list(header))
        rd = i2c_msg.read(self._addr, length)

        try:
            self._bus.i2c_rdwr(wr, rd)
        except IOError as e:
            logger.warning(f"IO error in I2C read: {e}")
            pass  # Silently handle IOError. Typically, see this when in bootloader mode
        
        time.sleep(0.001)

        return bytearray(list(rd)) # type: ignore # convert to list first to handle i2c_msg compatability 

    def write_page(self, target_address, length, payload: bytearray, ignore_return = False, bl_sync = False):
        assert length == len(payload)

        write_packet = bytearray(4)
        write_packet[0] = target_address & 0x00FF
        write_packet[1] = (target_address & 0xFF00) >> 8
        write_packet[2] = length & 0x00FF
        write_packet[3] = (length & 0x7F00) >> 8 # Read bit 0x80 is cleared by default

        write_packet.extend(payload[:length])

        wr = i2c_msg.write(self._addr, write_packet)

        try:
            self._bus.i2c_rdwr(wr)
            if bl_sync:
                # While bl is accumulating data, sync bits in the form of reading back 8 bytes is required.
                # this is done in a separate transaction.
                self.read_page(0x0100, 8)
        except IOError as e:
            if not ignore_return:
                logger.warning(f"IO error in I2C write: {e}")
            time.sleep(0.005)

        time.sleep(0.001)

    def close(self, u34_address, max_report_len):
        self._bus.close()
