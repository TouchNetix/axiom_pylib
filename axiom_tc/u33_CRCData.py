# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import struct
import logging

from axiom_usages.axiom_usages.usages import u33

logger = logging.getLogger(__name__)

class u33_CRCData(u33):
    USAGE_ID = 0x33

    def __init__(self, usage_bytes: bytearray, available_usages: list[int]):
        self._available_usages = available_usages

        self._raw = bytearray(self.USAGE_LEN) 

        self.set_bytes(usage_bytes[:self.USAGE_LEN])

    def print(self):
        self._print_registers()

    def compare_u33(self, other_u33: 'u33_CRCData'):
        overall_u33_ok = True
        do_u22_check = 0x22 in self._available_usages
        do_u43_check = 0x43 in self._available_usages
        do_u77_check = 0x77 in self._available_usages
        do_u93_check = 0x93 in self._available_usages
        do_u94_check = 0x94 in self._available_usages

        cfg_nvm_crc_ok = self.fld_nvltlusageconfig_crc == other_u33.fld_nvltlusageconfig_crc
        cfg_vltl_crc_ok = self.fld_vltusageconfig_crc == other_u33.fld_vltusageconfig_crc
        if not cfg_nvm_crc_ok or not cfg_vltl_crc_ok:
            overall_u33_ok = False

        logger.info("")
        logger.info(f"u33 Comparison                   {'Device'.center(10)} - {'File'.center(10)}")

        firmware_crc_ok = self.fld_runtime_crc == other_u33.fld_runtime_crc
        logger.info(
            f"  Firmware CRC                 : 0x{self.fld_runtime_crc:08X} - 0x{other_u33.fld_runtime_crc:08X} - "
            f"{'OK' if firmware_crc_ok else 'Config file saved from different version of firmware!'}"
        )

        logger.info(
            f"  Firmware Hash                : 0x{self.fld_runtimehash_crc:08X} - 0x{other_u33.fld_runtimehash_crc:08X} - N/A"
        )

        logger.info(
            f"  NVM Usage Config CRC         : 0x{self.fld_nvltlusageconfig_crc:08X} - 0x{other_u33.fld_nvltlusageconfig_crc:08X} - "
            f"{'OK' if cfg_nvm_crc_ok else 'MISMATCHED'}"
        )

        logger.info(
            f"  RAM Usage Config CRC         : 0x{self.fld_vltusageconfig_crc:08X} - 0x{other_u33.fld_vltusageconfig_crc:08X} - "
            f"{'OK' if cfg_vltl_crc_ok else 'MISMATCHED'}"
        )

        if do_u22_check:
            u22_ok = self.fld_u22_sequencedata_crc == other_u33.fld_u22_sequencedata_crc
            overall_u33_ok &= u22_ok
            logger.info(
                f"  u22 Sequence Data CRC        : 0x{self.fld_u22_sequencedata_crc:08X} - "
                f"0x{other_u33.fld_u22_sequencedata_crc:08X} - {'OK' if u22_ok else 'MISMATCHED'}"
            )

        if do_u43_check:
            u43_ok = self.fld_u43_hotspots_crc == other_u33.fld_u43_hotspots_crc
            overall_u33_ok &= u43_ok
            logger.info(
                f"  u43 Hotspots CRC             : 0x{self.fld_u43_hotspots_crc:08X} - "
                f"0x{other_u33.fld_u43_hotspots_crc:08X} - {'OK' if u43_ok else 'MISMATCHED'}"
            )

        if do_u77_check:
            if other_u33.REV < 3:
                logger.info(
                    f"  u77 DoD Calibration Data CRC : 0x{self.fld_u77_dod_calibration_data_crc:08X} - NOT PRESENT - SKIPPED"
                )
            else:
                u77_ok = self.fld_u77_dod_calibration_data_crc == other_u33.fld_u77_dod_calibration_data_crc
                overall_u33_ok &= u77_ok
                logger.info(
                    f"  u77 DoD Calibration Data CRC : 0x{self.fld_u77_dod_calibration_data_crc:08X} - "
                    f"0x{other_u33.fld_u77_dod_calibration_data_crc:08X} - {'OK' if u77_ok else 'MISMATCHED'}"
                )

        if do_u93_check:
            u93_ok = self.fld_u93_profiles_crc == other_u33.fld_u93_profiles_crc
            overall_u33_ok &= u93_ok
            logger.info(
                f"  u93 Profiles CRC             : 0x{self.fld_u93_profiles_crc:08X} - "
                f"0x{other_u33.fld_u93_profiles_crc:08X} - {'OK' if u93_ok else 'MISMATCHED'}"
            )

        if do_u94_check:
            u94_ok = self.fld_u94_deltascalemap_crc == other_u33.fld_u94_deltascalemap_crc
            overall_u33_ok &= u94_ok
            logger.info(
                f"  u94 Delta Scale Map CRC      : 0x{self.fld_u94_deltascalemap_crc:08X} - "
                f"0x{other_u33.fld_u94_deltascalemap_crc:08X} - {'OK' if u94_ok else 'MISMATCHED'}"
            )

        if overall_u33_ok:
            logger.info("All config CRCs match with the device configs!")

        return overall_u33_ok

    def _print_registers(self):
        logger.info("u33 CRC Data")
        logger.info(f"  Runtime CRC                  : 0x{self.fld_runtime_crc:08X}")
        logger.info(f"  Runtime NVM CRC              : 0x{self.fld_runtime_nvm_crc:08X}")
        logger.info(f"  Bootloader CRC               : 0x{self.fld_bootloader_crc:08X}")
        logger.info(f"  NVM Usage Config CRC         : 0x{self.fld_nvltlusageconfig_crc:08X}")
        logger.info(f"  RAM Usage Config CRC         : 0x{self.fld_vltusageconfig_crc:08X}")

        if 0x22 in self._available_usages:
            logger.info(f"  u22 Sequence Data CRC        : 0x{self.fld_u22_sequencedata_crc:08X}")

        if 0x43 in self._available_usages:
            logger.info(f"  u43 Hotspots CRC             : 0x{self.fld_u43_hotspots_crc:08X}")

        if 0x77 in self._available_usages:
            logger.info(f"  u77 DoD Calibration Data CRC : 0x{self.fld_u77_dod_calibration_data_crc:08X}")

        if 0x93 in self._available_usages:
            logger.info(f"  u93 Profiles CRC             : 0x{self.fld_u93_profiles_crc:08X}")

        if 0x94 in self._available_usages:
            logger.info(f"  u94 Delta Scale Map CRC      : 0x{self.fld_u94_deltascalemap_crc:08X}")

        logger.info(f"  Runtime Hash                 : 0x{self.fld_runtimehash_crc:08X}")