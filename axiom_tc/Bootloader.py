# Copyright (c) 2024 TouchNetix
#
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import os
import ctypes
import time
import logging

from .u31_DeviceInformation import u31_DeviceInformation
from .u02_SystemManager import u02_SystemManager

logger = logging.getLogger(__name__)

RESET_TIMEOUT = 2 # aXiom can take upto 2s to run through self tests at boot if they are all enabled
EXIT_BOOTLOADER_TIMEOUT = 10 #  aXiom can take upto 10s to exit bootloader occasionally
PAGE_SIZE = 256

class Bootloader:
    TIMEOUT_READS = 500

    # Bootloader protocol registers
    BLP_FIFO_ADDRESS = 0x0102
    BLP_REG_COMMAND = 0x0100
    BLP_REG_STATUS = 0x0100

    def __init__(self, comms, u02: u02_SystemManager | None = None, u31: u31_DeviceInformation| None = None):
        self._comms = comms
        self._u02 = u02
        self._u31 = u31

    def enter_bootloader_mode(self):

        if self._u02 is None:
            raise ReferenceError("u02 not loaded, cannot enter bootloader!")
        if self._u31 is None:
            raise ReferenceError("u31 not loaded, cannot enter bootloader!")
        
        # If the chip is already in bootloader mode, no need to continue
        if self._u31.is_in_bootloader_mode():
            return True

        # Attempt to enter bootloader mode via system manager
        system_manager_attempts = 5
        while system_manager_attempts > 0:
            # Entering bootloader mode is "involved" to ensure it is a deliberate
            # request. Three "enter bootloader" commands are required, the number
            # on the end is the sequence number, that will send the appropriate
            # "magic" number to aXiom. If all is well, aXiom will be in the
            # bootloader a few moments after the last command.
            self._u02.enter_bootloader()
            if self._u31.is_in_bootloader_mode():
                time.sleep(0.1) # ensure the bootloader is ready
                return True

            system_manager_attempts -= 1

        # Try toggle nreset line if available
        if hasattr(self._comms, "toggle_nreset"):
            nreset_attempts = 3
            while nreset_attempts > 0:
                for i in range(5):
                    self._comms.toggle_nreset() # do not send comms or else we cannot enter bootloader 
                
                if self._u31.is_in_bootloader_mode():
                    time.sleep(0.1) # ensure the bootloader is ready
                    return True
                        
                nreset_attempts -= 1
            
        # Failed to enter bootloader mode
        return False

    def _get_busy_status(self):
        status = self._comms.read_page(self.BLP_REG_STATUS, 4)
        # Busy bit is bit 0 of byte 2
        return (status[2] & 0x01) != 0

    def _precise_sleep(self, duration_seconds):
        if os.name == 'nt':  # Windows
            ctypes.windll.winmm.timeBeginPeriod(1)
            time.sleep(duration_seconds)
            ctypes.windll.winmm.timeEndPeriod(1)
        elif os.name == 'posix':  # Linux/Unix
            ctypes.CDLL('libc.so.6').usleep(int(duration_seconds * 1_000_000))  # Convert seconds to microseconds
        else:
            # An alternative approach to sleep for a precise duration
            # This approach can be CPU intensive.
            start = time.perf_counter()
            while (time.perf_counter() - start) < duration_seconds:
                pass

    def wait_until_not_busy(self):
        current_timeout = 0
        while self._get_busy_status():
            # aXiom is busy, wait 1ms before trying again
            if current_timeout < self.TIMEOUT_READS:
                current_timeout = current_timeout + 1
            else:
                raise TimeoutError("aXiom does not seem to be responding...")

            # If busy, allow the bootloader to run a bit longer before asking again.
            self._precise_sleep(0.001)

    def write_chunk(self, chunk: bytearray):
        offset = 0
        length = len(chunk)

        # The following slicing depends on the type of communication link.
        # here we probe the comms class to see if we have any USB specific
        # constants declared. If this is not the case then we assume chunk
        # size compatible with I2C/SPI.
        if self._comms.COMMS_TYPE == "USB":
            if self._comms.w_max_packet_size > PAGE_SIZE:
                chunk_size = (PAGE_SIZE - 1) - self._comms.AX_HEADER_LEN - self._comms.AX_USB_HEADER_LEN - self._comms.rd_base
            else:
                chunk_size = self._comms.max_wr_pay_length
        else:
            chunk_size = PAGE_SIZE - 1

        while offset < length:
            # Calculate how much data to transfer, up to the max transfer size
            if (offset + chunk_size) < length:
                length_to_write = chunk_size
            else:
                length_to_write = length - offset

            # Extract the data to be transferred
            payload_chunk = chunk[offset:(offset + length_to_write)]

            self._comms.write_page(self.BLP_FIFO_ADDRESS, length_to_write, payload_chunk, bl_sync = True, ignore_return=True)

            offset += length_to_write

        # Wait for decryption to complete
        self.wait_until_not_busy()
            