# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from .CDU_Common import CDU_Common
from .u02_SystemManager import u02_SystemManager
from .u31_DeviceInformation import u31_DeviceInformation
from .Bootloader import Bootloader


class axiom:
    TIMEOUT_MS = 5000  # timeout before giving up in comms

    # Usages to skip over, these are read only usages. If the config file
    # includes any of these usages, it is for informational purposes only
    ignore_usage_list = [0x31,  # Device Information
                         0x32,  # Device Capabilities
                         0x33,  # CRC Data
                         0x36,  # Factory calibration data
                         0x82]  # AE Controls

    # Command driven usages. They can contain a large amount of data which is
    # in efficient for aXiom to store in RAM. These usages need to be handled
    # slightly differently from normal usages.
    cdu_usage_list = [0x05,  # Comments
                      0x22,  # Sequence Data
                      0x43,  # Haptic Hotspots
                      0x77,  # Dial on Display
                      0x93,  # AE Profile
                      0x94]  # Delta scale map

    def __init__(self, comms, read_usage_table=True):
        self._comms = comms

        # Pass the axiom object into comms for access to axiom data and methods
        comms.comms_init(self)

        # Objects to usages that are key to most axiom operations, however, most cannot be
        # used if the device is in bootloader mode.
        self.u31 = u31_DeviceInformation(self, read_usage_table)

        if self.is_in_bootloader_mode():
            self.u02 = None
        else:
            self.u02 = u02_SystemManager(self)

    def read_usage(self, usage, length=None):
        usage_content = []

        for pg in range(0, self.u31.usage_table[usage].num_pages):
            # Calculate the remaining data to read for the last page
            if pg == (self.u31.usage_table[usage].num_pages - 1):
                read_length = self.u31.usage_table[usage].length - (self.u31.PAGE_SIZE * pg)
            else:
                read_length = self.u31.PAGE_SIZE

            # If the user requests a specific amount of data, calculate how much data to read
            # for this page.
            if length is not None:
                if length > self.u31.usage_table[usage].length:
                    # Someone has requested more data than is available by the usage. Leave
                    # read_length unmodified, this will effectively cap the read length to
                    # the size of the usage.
                    pass
                elif (self.u31.PAGE_SIZE * (pg + 1)) > length:
                    # Recalculate the read_length based on the length request.
                    read_length = length - (self.u31.PAGE_SIZE * pg)

            target_address = self.u31.convert_usage_to_target_address(usage, pg)
            usage_content += self._comms.read_page(target_address, read_length)

            if read_length < self.u31.PAGE_SIZE:
                # Not a full page was required, therefore exit the loop early.
                break

        return usage_content

    def write_usage(self, usage, buffer):
        buffer_offset = 0

        for pg in range(0, self.u31.usage_table[usage].num_pages):
            write_length = self.u31.PAGE_SIZE

            # Calculate the remaining data to read for the last page
            if pg == (self.u31.usage_table[usage].num_pages - 1):
                write_length = self.get_usage_length(usage) - (self.u31.PAGE_SIZE * pg)

            buffer_offset_end = buffer_offset + write_length
            target_address = self.u31.convert_usage_to_target_address(usage, pg)

            self._comms.write_page(target_address, write_length, buffer[buffer_offset:buffer_offset_end])
            self.u02.check_usage_write_progress(usage)

            buffer_offset += self.u31.PAGE_SIZE

    def get_usage_revision(self, usage):
        if not self.u31.usage_table_populated:
            revision = 0
        else:
            revision = self.u31.usage_table[usage].usage_rev
        return revision

    def get_usage_length(self, usage):
        if self.u31.usage_table_populated:
            return self.u31.usage_table[usage].length
        else:
            return 0

    def is_in_bootloader_mode(self):
        u31_ta = 0x0000
        u31_page0 = self._comms.read_page(u31_ta, 12)
        return True if (u31_page0[1] & 0x80) else False

    def config_write_usage_to_device(self, usage, buffer):
        if usage in self.ignore_usage_list:  # These are informational usages or read only
            pass
        elif usage in self.cdu_usage_list:  # Command driven usages need to be handled separately
            cdu = CDU_Common(self)
            cdu.write(usage, buffer)
            cdu_content = cdu.read(usage)

            if buffer != cdu_content:
                print("ERROR: Failed to write CDU contents. u%02X" % usage)
        else:
            self.write_usage(usage, buffer)
            usage_buffer = self.read_usage(usage)

            if buffer != usage_buffer:
                print("ERROR: Failed to write config to usage 0x%x" % usage)
                print("Expected Length: %d and Actual Length: %d" % (len(buffer), len(usage_buffer)))
                print("Expecting: " + str(buffer))
                print("Read from Device: " + str(usage_buffer))

    def close(self):
        self._comms.close()
