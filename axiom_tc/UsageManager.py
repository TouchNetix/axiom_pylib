# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import logging

logger = logging.getLogger(__name__)

from .u02_SystemManager import u02_SystemManager

class UsageManager:
    PAGE_SIZE = 256

    def __init__(self, comms, u02: u02_SystemManager):
        """
        Initializes the UsageManager with a communication interface.
        
        :param comms: The communication object providing read_page and write_page methods.
        """
        self._comms = comms
        self._u02 = u02

    def get_page_offset_address(self, address, page=0):
        """Calculates the address for a specific page offset."""
        return address + (page << 8)

    def write(self, usage_address, usage_length, buffer, skip_check=False):
        """
        Writes data to the device, handling pagination and optional progress checking.
        """
        assert len(buffer) == usage_length, (
            f"Usage length ({usage_length}) and buffer length ({len(buffer)}) do not match."
        )
        
        num_pages = (usage_length + self.PAGE_SIZE - 1) // self.PAGE_SIZE

        for pg in range(num_pages):
            buffer_offset = pg * self.PAGE_SIZE
            
            # Calculate the remaining data to write
            write_length = min(self.PAGE_SIZE, usage_length - buffer_offset)
            buffer_offset_end = buffer_offset + write_length

            page_address = self.get_page_offset_address(usage_address, pg)
            self._comms.write_page(page_address, write_length, buffer[buffer_offset:buffer_offset_end])


        if self._u02:
            self._u02.wait_for_idle(timeout=1)        

        if not skip_check:

            usage_buffer = self.read(usage_address, usage_length)
     
            if buffer != usage_buffer:
                logger.debug(f"Failed to verify write at address 0x{usage_address:04x}")
                if len(buffer) != len(usage_buffer):
                    logger.debug(f"Expected Length: {len(buffer)}, Actual Length: {len(usage_buffer)}")
                else:
                    logger.debug(f"Expecting: {list(buffer)}")
                    logger.debug(f"Read from Device: {list(usage_buffer)}")
                    logger.debug("This is expected if attempting to write to a read-only field.")

    def read(self, usage_address, usage_length) -> bytearray:
        """
        Reads data from the device, handling pagination.
        """
        usage_content = bytearray()
        num_pages = (usage_length + self.PAGE_SIZE - 1) // self.PAGE_SIZE

        remaining_length = usage_length
        for pg in range(num_pages):
            read_length = min(self.PAGE_SIZE, remaining_length)

            page_address = self.get_page_offset_address(usage_address, pg)
            usage_content += self._comms.read_page(page_address, read_length)

            remaining_length -= read_length
            if remaining_length <= 0:
                break

        return usage_content
    