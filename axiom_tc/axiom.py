# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import time
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

        if self.is_in_bootloader_mode() or not self.u31.usage_table_populated or 0x02 not in self.u31.usage_table:
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
        if not self.u31.usage_table_populated or usage not in self.u31.usage_table:
            revision = 0
        else:
            revision = self.u31.usage_table[usage].usage_rev
        return revision

    def get_usage_length(self, usage):
        if self.u31.usage_table_populated and usage in self.u31.usage_table:
            return self.u31.usage_table[usage].length
        else:
            return 0

    def is_in_bootloader_mode(self):
        u31_ta = 0x0000
        try:
            u31_page0 = self._comms.read_page(u31_ta, 12)
            if not u31_page0 or len(u31_page0) < 12:
                return True
            return True if (u31_page0[1] & 0x80) or (u31_page0[0] == 0 and u31_page0[1] == 0) else False
        except Exception:
            return True

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

    def wait_for_u01_report(self, timeout=15.0):
        """
        Polls u34 for a u01 System Manager report confirming startup completion.
        """
        if not self.u31.usage_table_populated or 0x34 not in self.u31.usage_table:
            return False

        u34_address = self.u31.convert_usage_to_target_address(0x34)
        report_length = self.u31.max_report_len

        start_time = time.time()
        can_get_irq = hasattr(self._comms, "get_irq_state")

        while (time.time() - start_time) < timeout:
            if can_get_irq:
                irq_state = self._comms.get_irq_state()
                if irq_state is None:
                    can_get_irq = False  # 0xE3 unsupported, switch to polling
                elif not irq_state:
                    time.sleep(0.010)
                    continue

            try:
                report_bytes = self._comms.read_page(u34_address, report_length)
                if report_bytes and len(report_bytes) >= 2:
                    # Byte 0 bit 7 = 0 (valid data), Byte 1 = 0x01 (u01 System Manager)
                    if (report_bytes[0] & 0x80) == 0 and report_bytes[1] == 0x01:
                        time.sleep(0.050)  # Safety settle delay after u01 report
                        return True
            except Exception:
                pass

            time.sleep(0.050)

        return False

    def reset_axiom(self, timeout=15.0):
        """
        Resets the device and waits for it to become ready in runtime mode.
        """
        if self.is_in_bootloader_mode():
            Bootloader(self, self._comms).reset_axiom()
        elif self.u02 is not None:
            self.u02.send_command(self.u02.CMD_SOFT_RESET)

        time.sleep(0.150)

        # Poll until device info (u31) is valid and usage table is built
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.u31.build_usage_table():
                break
            time.sleep(0.100)
        else:
            print("ERROR: Device timed out waiting for runtime device info.")
            return False

        if not self.wait_for_u01_report(timeout=timeout):
            print("ERROR: Timed out waiting for aXiom boot report (u01).")
            return False

        if 0x02 in self.u31.usage_table:
            self.u02 = u02_SystemManager(self)

        return True

    def close(self):
        self._comms.close()
