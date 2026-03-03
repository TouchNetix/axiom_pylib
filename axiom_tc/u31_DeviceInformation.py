# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from typing import Dict
import logging
import time
from enum import Enum

from axiom_usages.axiom_usages.usages import u31

logger = logging.getLogger(__name__)

PAGE_SIZE = 256
TIMEOUT_READS = 3  # timeout before giving up in comms

class _Usage_Table_Entry:
    USAGE_TABLE_ENTRY_SIZE = 6

    def __init__(self, id, start_page, num_pages, max_offset, offset_type, usage_rev, usage_type, length=None):
        self.id = id
        self.start_page = start_page
        self.num_pages = num_pages
        self.is_report = True if (num_pages == 0) else False
        self.max_offset = max_offset
        self.offset_type = offset_type
        self.usage_rev = usage_rev
        self.length = length or self._calc_length()
        self.type = usage_type

    def __str__(self):
        return (
            f"Usage: u{self.id:02x}    "
            f"Rev: {self.usage_rev:3d}    "
            f"Page: 0x{self.start_page:02x}00    "
            f"Num Pages: {self.num_pages:3d}    "
            f"Length: {self.length:5d}    "
            f"{self.type.name}"
        )

    def _calc_length(self) -> int:
        if self.num_pages == 0:
            length = (self.max_offset + 1) * 2
        else:
            length = ((self.num_pages - 1) * PAGE_SIZE) + ((self.max_offset + 1) * 2)

        return length
    
class u31_DeviceInformation(u31):
    USAGE_ID = 0x31
    u31_TARGET_ADDRESS = 0x0000
    u31_PAGE_0_LEN = 12 # must be less than PAGE_SIZE
    USAGE_TABLE_ENTRY_SIZE = 6
    
    FW_VARIANTS = ["3D", "2D", "FORCE", "0D", "XL", "TOUCHPAD"]
    FW_STATUS = ["eng", "prod"]
    usage_table_populated = False
    max_report_len = 0

    def __init__(self, comms, read=True):
        self._comms = comms
        self._usage_table: Dict[int, _Usage_Table_Entry] = {}
        self._raw = bytearray()

        # load usage table 
        if read:
            self.read_all()

        return

    def read_all(self):

        self._read_device_info()

        if self.fld_mode == self.MODE_Enum.BOOTLOADER_BLP_:
            logger.debug("aXiom device is in bootloader, usage table will not be populated.")
            return
        
        self._read_usage_table()

        self.build_usage_table()
    
    def is_report(self, usage):
        if self._usage_table[usage].type == self.USAGE_TYPE_0_Enum.REPORT:
            return True
        else:
            return False

    def is_read_only(self, usage):
        if not self.usage_table_populated:
            raise LookupError("u31 usage table not yet populated!")
        
        if usage not in self._usage_table.keys():
            raise LookupError(f"usage u{usage} does not exist!")

        if self._usage_table[usage].type in [self.USAGE_TYPE_0_Enum.REGISTER_READ_ONLY_, 
                                             self.USAGE_TYPE_0_Enum.CDU_READ_ONLY_,
                                             self.USAGE_TYPE_0_Enum.OTHER]:
            return True
        else:
            return False
        
    def is_cdu(self, usage):
        if not self.usage_table_populated:
            raise LookupError("u31 usage table not yet populated!")
        
        if usage not in self._usage_table.keys():
            raise LookupError(f"usage u{usage} does not exist!")

        if self._usage_table[usage].type in [self.USAGE_TYPE_0_Enum.CDU, self.USAGE_TYPE_0_Enum.CDU_READ_ONLY_]:
            return True
        else:
            return False
        
    def get_usage_vers(self) -> dict[int, int]:
        """
        Returns a dict mapping usage ID (int) to revision number (int).
        Example: { 1: 3, 31: 1, 0xF3: 1 }
        """
        usage_vers = {}

        if not self.usage_table_populated:
            raise Exception("u31 usage table not yet populated.")

        for usage_id, entry in self._usage_table.items():
            usage_vers[usage_id] = entry.usage_rev

        return usage_vers
    
    def _read_usage_table(self):

        target_address = self.get_usage_page_address(self.USAGE_ID, 1)
        
        # get the whole usage table in a single buffer
        raw_usage_table = self._comms.read_page(target_address, self.fld_num_usages * self.USAGE_TABLE_ENTRY_SIZE)
        
        self._raw[PAGE_SIZE : PAGE_SIZE + len(raw_usage_table)] = raw_usage_table

    def _read_device_info(self):
        
        device_info_len = self.u31_PAGE_0_LEN

        if not len(self._raw):
            self._raw = bytearray(device_info_len)

        for _ in range(TIMEOUT_READS):
            raw_device_info = self._comms.read_page(self.u31_TARGET_ADDRESS, device_info_len)

            self._raw[:len(raw_device_info)] = raw_device_info

            # TODO use another feature to verify the device info is valid?
            if max(raw_device_info) > 0 and self.fld_tcp_revision == 1:
                break
                
            logger.debug("Invalid device info, retrying...")
            time.sleep(0.1)
        else:
            raise AssertionError("aXiom device info unavailable.")

        # device info maps onto 1st page, usage table maps onto following pages
        u31_length = PAGE_SIZE + self.fld_num_usages * self.USAGE_TABLE_ENTRY_SIZE
        if len(self._raw) < u31_length:
            self._raw.extend(bytearray(u31_length - len(self._raw)))
        
        
    def get_usage_address(self, usage) -> int:
        if usage == 0x31:
            target_address = 0x0000
        elif not self.usage_table_populated:
            raise Exception("u31 usage table not yet populated.")
        elif usage not in self._usage_table.keys():
            raise Exception(f"unsupported usage: u{usage:02X}")
        else:
            target_address = (self._usage_table[usage].start_page << 8)

        return target_address
    
    def get_usage_page_address(self, usage, page):
        return self.get_usage_address(usage) + (page << 8)
    
    def get_usages(self):
        return self._usage_table.keys()
    
    def get_usage_table(self):
        return self._usage_table.copy()

    def get_usage_entry(self, usage):
        if usage not in self._usage_table.keys():
            raise Exception(f"unsupported usage: u{usage:02X}")

        return self._usage_table[usage]

    def _calculate_usage_length(self, num_usages, id, num_pages, max_offset):
        if num_pages == 0:
            length = (max_offset + 1) * 2
        elif id == self.USAGE_ID:
            length = PAGE_SIZE + (num_usages * 6)
        else:
            length = ((num_pages - 1) * PAGE_SIZE) + ((max_offset + 1) * 2)

        return length
    
    def _set_repeats(self):
        self.fld_usage_num_0.set_repeat_count(self.fld_num_usages)
        self.fld_start_page_0.set_repeat_count(self.fld_num_usages)
        self.fld_num_pages_0.set_repeat_count(self.fld_num_usages)
        self.fld_max_offset_0.set_repeat_count(self.fld_num_usages)
        self.fld_offset_type_0.set_repeat_count(self.fld_num_usages)
        self.fld_uifrevision_0.set_repeat_count(self.fld_num_usages)
        self.fld_usage_type_0.set_repeat_count(self.fld_num_usages)

    def build_usage_table(self):
        
        self._set_repeats()

        for i in range(self.fld_num_usages):
            usage_id = self.fld_usage_num_0[i]
            if usage_id == self.USAGE_ID:
                u31_length = PAGE_SIZE + (self.fld_num_usages * 6)
            else:
                u31_length = None
            entry = _Usage_Table_Entry(
                id          = usage_id,
                start_page  = self.fld_start_page_0[i],
                num_pages   = self.fld_num_pages_0[i],
                max_offset  = self.fld_max_offset_0[i],
                offset_type = self.fld_offset_type_0[i],
                usage_rev   = self.fld_uifrevision_0[i],
                usage_type       = self.fld_usage_type_0[i],
                length      = u31_length,
            )

            self._usage_table[entry.id] = entry
            if entry.is_report:
                self.max_report_len = max(self.max_report_len, entry.length)
                
        if not (0x31 in self._usage_table):
            raise ValueError("Invalid usage table, axiom may not be available!")
        
        self.usage_table_populated = True

    def print_usage_table(self):
        if not self.usage_table_populated:
            raise Exception("u31 usage table not yet populated.")
    
        logger.info("Usage Table:")
        for u in self._usage_table:
            logger.info(f"{self._usage_table[u]}")

    def print_device_info(self):
        silicon_rev = chr(0x41 + self.fld_silicon_revision)

        logger.info("u31 Device Information:")
        logger.info(f"  Device ID   : {self.convert_device_id_to_string(self.fld_device_id)}")
        logger.info(
            "  FW Revision : "
            f"{self.convert_firmware_version_to_string(self.fld_mode, self.fld_runtime_fw_rev_major, self.fld_runtime_fw_rev_minor, self.fld_runtime_fw_rev_patch, self.fld_runtime_fw_status, self.fld_device_build_variant)}"
        )
        logger.info(f"  BL Revision : {self.fld_bootloader_fw_rev_major}.{self.fld_bootloader_fw_rev_minor:02d}")
        logger.info(f"  Silicon     : 0x{self.fld_jedec_id:04X} (Rev {silicon_rev})")
    
    def convert_device_id_to_string(self, device_id):
        device_channel_count = device_id & 0x3FF
        device_variant = (device_id & 0x7C00) >> 10
        return "AX%u%c" % (device_channel_count, chr(ord('A') + device_variant))

    def get_device_info_short(self):
        
        device_str = self.convert_device_id_to_string(self.fld_device_id)
        fw_str = self.convert_firmware_version_to_string(
            self.fld_mode,
            self.fld_runtime_fw_rev_major,
            self.fld_runtime_fw_rev_minor,
            self.fld_runtime_fw_rev_patch,
            self.fld_runtime_fw_status,
            self.fld_device_build_variant
        )
        return f"{device_str} {fw_str}"
    
    def is_in_bootloader_mode(self):
        try:
            self._read_device_info()
        except:
            return True # fallback to BL if device info is unavailable due to a comms issue

        if self.fld_mode == self.MODE_Enum.BOOTLOADER_BLP_:
            logger.debug("aXiom device is in bootloader mode.")
            return True
        else:
            logger.debug("aXiom device is not in bootloader mode.")
            return False
        
    def convert_firmware_version_to_string(self, mode, major, minor, patch, status, fw_variant):

        if isinstance(mode, Enum):
            mode = mode.value

        if mode == self.MODE_Enum.RUNTIME_TCP_.value:
            fw_status = self.FW_STATUS[status]
            fw_var = self.FW_VARIANTS[fw_variant]

            if major >= 4 and minor >= 8:
                return f"{major}.{minor}.{patch}-{fw_status} {fw_var}"
            else:
                return f"{major}.{minor:02d}-{fw_status} (RC{patch}) {fw_var}"
        else:
            return f"Bootloader {major}.{minor:02d}"
        
    def get_supported_usages(self):
        return list(self._usage_table.keys())
    