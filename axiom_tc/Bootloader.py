# Copyright (c) 2024 TouchNetix
#
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from time import sleep


class Bootloader:
    # Bootloader protocol registers
    BLP_FIFO_ADDRESS = 0x0102
    BLP_REG_COMMAND = 0x0100
    BLP_REG_STATUS = 0x0100

    def __init__(self, axiom=None, comms=None):
        self._axiom = axiom
        self._comms = comms

    def enter_bootloader_mode(self):
        attempts = 5

        # If the chip is already in bootloader mode, no need to continue
        if self._axiom.is_in_bootloader_mode():
            return True

        # Depending on the sequence, the usage table may not be populated at
        # this moment. The device is not in bootloader mode, so it should be
        # safe to build the usage table. The usage table is required to send the
        # appropriate system manager commands to aXiom to get it into bootloader
        # mode
        if not self._axiom.u31.usage_table_populated:
            self._axiom.u31.build_usage_table()

        # Attempt to enter bootloader mode
        while (not self._axiom.is_in_bootloader_mode()) and (attempts > 0):
            # Entering bootloader mode is "involved" to ensure it is a deliberate
            # request. Three "enter bootloader" commands are required, the number
            # on the end is the sequence number, that will send the appropriate
            # "magic" number to aXiom. If all is well, aXiom will be in the
            # bootloader a few moments after the last command.
            self._axiom.u02.send_command(self._axiom.u02.CMD_ENTER_BOOTLOADER)

            # Check if the device is in bootloader mode
            if self._axiom.is_in_bootloader_mode():
                # Bootloader flag is set, no need to continue.
                return True

            attempts -= 1

        # Failed to enter bootloader mode
        return False

    def _get_busy_status(self):
        status = self._comms.read_page(self.BLP_REG_STATUS, 4)
        # Busy bit is bit 0 of byte 2
        return (status[2] & 0x01) != 0

    def _wait_until_not_busy(self):
        current_timeout = 0
        while self._get_busy_status():
            # aXiom is busy, wait 1ms before trying again
            if current_timeout < self._axiom.TIMEOUT_MS:
                current_timeout = current_timeout + 1
            else:
                print("ERROR: aXiom does not seem to be responding...")
                raise TimeoutError

            # If busy, allow the bootloader to run a bit longer before asking again
            sleep(0.001)

    def reset_axiom(self):
        self._comms.write_page(self.BLP_REG_COMMAND, 2, [0x02, 0x00])

    def write_chunk(self, chunk):
        # Ensure aXiom is available to process our request
        self._wait_until_not_busy()

        offset = 0
        length = len(chunk)

        # The following slicing depends on the type of communication link.
        # here we probe the comms class to see if we have any USB specific
        # constants declared. If this is not the case then we assume chunk
        # size compatible with I2C/SPI.
        try:
            if self._comms.wMaxPacketSize > self._axiom.u31.PAGE_SIZE:
                chunk_size = (self._axiom.u31.PAGE_SIZE - 1) - self._comms.AX_HEADER_LEN
            else:
                chunk_size = (self._comms.wMaxPacketSize - 1) \
                             - self._comms.AX_TBP_I2C_DEV_HEAD_LEN \
                             - self._comms.AX_HEADER_LEN
        except AttributeError:
            chunk_size = self._axiom.u31.PAGE_SIZE - 1

        while offset < length:
            # Calculate how much data to transfer, up to the max transfer size
            if (offset + chunk_size) < length:
                length_to_write = chunk_size
            else:
                length_to_write = length - offset

            # Extract the data to be transferred
            payload_chunk = chunk[offset:(offset + length_to_write)]

            # Send the data to aXiom
            self._comms.write_page(self.BLP_FIFO_ADDRESS, length_to_write, payload_chunk)

            # Ensure aXiom is available to process our request
            self._wait_until_not_busy()
            offset += length_to_write
