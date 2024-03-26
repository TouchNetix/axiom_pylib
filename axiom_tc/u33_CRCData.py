# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import struct


class u33_CRCData:
    USAGE_ID = 0x33

    def __init__(self, axiom, read=True):
        self._axiom = axiom

        # Get the usage number from the axiom class
        self._usage_revision = self._axiom.get_usage_revision(self.USAGE_ID)

        # Initialise a buffer for the usage's contents to be read into and unpacked/packed
        self._usage_binary_data = [0] * self._axiom.get_usage_length(self.USAGE_ID)

        self.init_usage()

        # Initialise the variables that are supported by this revision of the usage.
        # With new firmware, the usage could be up-revved and new methods will need
        # to be added
        self._init_registers()

        # Populate the registers by reading the device
        if read:
            self.read()

    def read(self):
        self._usage_binary_data = self._axiom.read_usage(self.USAGE_ID)
        self._unpack()

    def write(self):
        self.read()
        raise Exception("Cannot write to u33. u33 is a read-only usage.")

    def print(self):
        self._print_registers()

    def init_usage(self):
        # To handle different usage revisions, there are different methods that handle
        # register initialisation (in this python class), dumping out the contents of
        # a usage and unpacking and packing the usage's variables back into binary formats.
        # Use the getattr() find find the appropriate methods that pertain the usage revision.
        self._init_registers = getattr(self, "_init_registers_uifrev{}".format(self._usage_revision), None)
        self._print_registers = getattr(self, "_print_registers_uifrev{}".format(self._usage_revision), None)
        self._unpack_registers = getattr(self, "_unpack_uifrev{}".format(self._usage_revision), None)

        # Raise an exception if an unsupported version of the usage is found.
        if (self._init_registers is None or
                self._print_registers is None or
                self._unpack_registers is None):
            raise Exception(
                "Unsupported revision of {}. Revision: {}".format(self.__class__.__name__, self._usage_revision))

    def _unpack(self):
        self._unpack_registers()

    # region u33 Specific Methods
    def compare_u33(self, other_u33, print_results=False):
        overall_u33_ok = True
        do_u22_check = self._axiom.u31.is_usage_present_on_device(0x22)
        do_u43_check = self._axiom.u31.is_usage_present_on_device(0x43)
        do_u77_check = self._axiom.u31.is_usage_present_on_device(0x77)
        do_u93_check = self._axiom.u31.is_usage_present_on_device(0x93)
        do_u94_check = self._axiom.u31.is_usage_present_on_device(0x94)

        cfg_nvm_crc_ok = self.reg_nvltl_usage_config_crc == other_u33.reg_nvltl_usage_config_crc
        if not cfg_nvm_crc_ok:
            overall_u33_ok = False

        cfg_vltl_crc_ok = self.reg_vltl_usage_config_crc == other_u33.reg_vltl_usage_config_crc
        if not cfg_vltl_crc_ok:
            overall_u33_ok = False

        if print_results:
            print("")
            print("u33 Comparison                   %10s - %10s" % ("Device".center(10), "File".center(10)))

            firmware_crc_ok = self.reg_runtime_crc == other_u33.reg_runtime_crc
            print("  Firmware CRC                 : 0x%08X - 0x%08X - %s" % (
                self.reg_runtime_crc, other_u33.reg_runtime_crc,
                "OK" if firmware_crc_ok else "Config file saved from different version of firmware!"))
            print("  Firmware Hash                : 0x%08X - 0x%08X - N/A" % (
                self.reg_runtime_hash, other_u33.reg_runtime_hash))
            print("  NVM Usage Config CRC         : 0x%08X - 0x%08X - %s" % (
                self.reg_nvltl_usage_config_crc, other_u33.reg_nvltl_usage_config_crc,
                "OK" if cfg_nvm_crc_ok else "MISMATCHED"))
            print("  RAM Usage Config CRC         : 0x%08X - 0x%08X - %s" % (
                self.reg_vltl_usage_config_crc, other_u33.reg_vltl_usage_config_crc,
                "OK" if cfg_vltl_crc_ok else "MISMATCHED"))

        if do_u22_check:
            u22_ok = self.reg_u22_sequence_data_cdu_crc == other_u33.reg_u22_sequence_data_cdu_crc
            if not u22_ok:
                overall_u33_ok = False
            if print_results:
                print("  u22 Sequence Data CRC        : 0x%08X - 0x%08X - %s" % (
                    self.reg_u22_sequence_data_cdu_crc, other_u33.reg_u22_sequence_data_cdu_crc,
                    "OK" if u22_ok else "MISMATCHED"))

        if do_u43_check:
            u43_ok = self.reg_u43_hotspots_cdu_crc == other_u33.reg_u43_hotspots_cdu_crc
            if not u43_ok:
                overall_u33_ok = False
            if print_results:
                print("  u43 Hotspots CRC             : 0x%08X - 0x%08X - %s" % (
                    self.reg_u43_hotspots_cdu_crc, other_u33.reg_u43_hotspots_cdu_crc,
                    "OK" if u43_ok else "MISMATCHED"))

        if do_u77_check:
            if other_u33._usage_revision < 3:
                # The "other" u33 doesn't contain u77, skip it and assume CRC is OK
                if print_results:
                    print("  u77 DoD Calibration Data CRC : 0x%08X - NOT PRESENT - SKIPPED" % (
                        self.reg_u77_dod_calibration_data_crc))
            else:
                u77_ok = self.reg_u77_dod_calibration_data_crc == other_u33.reg_u77_dod_calibration_data_crc
                if not u77_ok:
                    overall_u33_ok = False
                if print_results:
                    print("  u77 DoD Calibration Data CRC : 0x%08X - 0x%08X - %s" % (
                        self.reg_u77_dod_calibration_data_crc, other_u33.reg_u77_dod_calibration_data_crc,
                        "OK" if u77_ok else "MISMATCHED"))

        if do_u93_check:
            u93_ok = self.reg_u93_profiles_cdu_crc == other_u33.reg_u93_profiles_cdu_crc
            if not u93_ok:
                overall_u33_ok = False
            if print_results:
                print("  u93 Profiles CRC             : 0x%08X - 0x%08X - %s" % (
                    self.reg_u93_profiles_cdu_crc, other_u33.reg_u93_profiles_cdu_crc,
                    "OK" if u93_ok else "MISMATCHED"))

        if do_u94_check:
            u94_ok = self.reg_u94_delta_scale_map_cdu_crc == other_u33.reg_u94_delta_scale_map_cdu_crc
            if not u94_ok:
                overall_u33_ok = False
            if print_results:
                print("  u94 Delta Scale Map CRC      : 0x%08X - 0x%08X - %s" % (
                    self.reg_u94_delta_scale_map_cdu_crc, other_u33.reg_u94_delta_scale_map_cdu_crc,
                    "OK" if u94_ok else "MISMATCHED"))

        return overall_u33_ok

    # endregion

    # region u33 Usage Name Usage Revision 1
    def _init_registers_uifrev1(self):
        self.reg_runtime_crc = 0
        self.reg_runtime_nvm_crc = 0
        self.reg_bootloader_crc = 0
        self.reg_nvltl_usage_config_crc = 0
        self.reg_vltl_usage_config_crc = 0
        self.reg_u05_comments_crc = 0
        self.reg_u22_sequence_data_cdu_crc = 0
        self.reg_u43_hotspots_cdu_crc = 0
        self.reg_u93_profiles_cdu_crc = 0
        self.reg_u94_delta_scale_map_cdu_crc = 0
        self.reg_runtime_hash = 0

    def _unpack_uifrev1(self):
        (rt_crc, rt_nvm_crc, bl_crc, nvltl_config_crc, vltl_config_crc, u05_crc, u22_crc, u43_crc, u93_crc, u94_crc,
         hash) = struct.unpack(
            "<11I", bytes(bytearray(self._usage_binary_data[0:44])))
        self.reg_runtime_crc = rt_crc
        self.reg_runtime_nvm_crc = rt_nvm_crc
        self.reg_bootloader_crc = bl_crc
        self.reg_nvltl_usage_config_crc = nvltl_config_crc
        self.reg_vltl_usage_config_crc = vltl_config_crc
        self.reg_u05_comments_crc = u05_crc
        self.reg_u22_sequence_data_cdu_crc = u22_crc
        self.reg_u43_hotspots_cdu_crc = u43_crc
        self.reg_u93_profiles_cdu_crc = u93_crc
        self.reg_u94_delta_scale_map_cdu_crc = u94_crc
        self.reg_runtime_hash = hash

    def _print_registers_uifrev1(self):
        print("u33 CRC Data")
        print("  Runtime CRC             : 0x{:08X}".format(self.reg_runtime_crc))
        print("  Runtime NVM CRC         : 0x{:08X}".format(self.reg_runtime_nvm_crc))
        print("  Bootloader CRC          : 0x{:08X}".format(self.reg_bootloader_crc))
        print("  NVM Usage Config CRC    : 0x{:08X}".format(self.reg_nvltl_usage_config_crc))
        print("  RAM Usage Config CRC    : 0x{:08X}".format(self.reg_vltl_usage_config_crc))

        if self._axiom.u31.is_usage_present_on_device(0x05):
            print("  u05 Comments CRC        : 0x{:08X}".format(self.reg_u05_comments_crc))

        if self._axiom.u31.is_usage_present_on_device(0x22):
            print("  u22 Sequence Data CRC   : 0x{:08X}".format(self.reg_u22_sequence_data_cdu_crc))

        if self._axiom.u31.is_usage_present_on_device(0x43):
            print("  u43 Hotspots CRC        : 0x{:08X}".format(self.reg_u43_hotspots_cdu_crc))

        if self._axiom.u31.is_usage_present_on_device(0x93):
            print("  u93 Profiles CRC        : 0x{:08X}".format(self.reg_u93_profiles_cdu_crc))

        if self._axiom.u31.is_usage_present_on_device(0x94):
            print("  u94 Delta Scale Map CRC : 0x{:08X}".format(self.reg_u94_delta_scale_map_cdu_crc))
        print("  Runtime Hash            : 0x{:08X}".format(self.reg_runtime_hash))

    # endregion

    # region u33 Usage Name Usage Revision 2
    def _init_registers_uifrev2(self):
        self.reg_runtime_crc = 0
        self.reg_runtime_nvm_crc = 0
        self.reg_bootloader_crc = 0
        self.reg_nvltl_usage_config_crc = 0
        self.reg_vltl_usage_config_crc = 0
        self.reg_u22_sequence_data_cdu_crc = 0
        self.reg_u43_hotspots_cdu_crc = 0
        self.reg_u93_profiles_cdu_crc = 0
        self.reg_u94_delta_scale_map_cdu_crc = 0
        self.reg_runtime_hash = 0

    def _unpack_uifrev2(self):
        rt_crc, rt_nvm_crc, bl_crc, nvltl_config_crc, vltl_config_crc, u22_crc, u43_crc, u93_crc, u94_crc, hash = (
            struct.unpack("<10I", bytes(bytearray(self._usage_binary_data[0:40]))))
        self.reg_runtime_crc = rt_crc
        self.reg_runtime_nvm_crc = rt_nvm_crc
        self.reg_bootloader_crc = bl_crc
        self.reg_nvltl_usage_config_crc = nvltl_config_crc
        self.reg_vltl_usage_config_crc = vltl_config_crc
        self.reg_u22_sequence_data_cdu_crc = u22_crc
        self.reg_u43_hotspots_cdu_crc = u43_crc
        self.reg_u93_profiles_cdu_crc = u93_crc
        self.reg_u94_delta_scale_map_cdu_crc = u94_crc
        self.reg_runtime_hash = hash

    def _print_registers_uifrev2(self):
        print("u33 CRC Data")
        print("  Runtime CRC             : 0x{:08X}".format(self.reg_runtime_crc))
        print("  Runtime NVM CRC         : 0x{:08X}".format(self.reg_runtime_nvm_crc))
        print("  Bootloader CRC          : 0x{:08X}".format(self.reg_bootloader_crc))
        print("  NVM Usage Config CRC    : 0x{:08X}".format(self.reg_nvltl_usage_config_crc))
        print("  RAM Usage Config CRC    : 0x{:08X}".format(self.reg_vltl_usage_config_crc))

        if self._axiom.u31.is_usage_present_on_device(0x22):
            print("  u22 Sequence Data CRC   : 0x{:08X}".format(self.reg_u22_sequence_data_cdu_crc))

        if self._axiom.u31.is_usage_present_on_device(0x43):
            print("  u43 Hotspots CRC        : 0x{:08X}".format(self.reg_u43_hotspots_cdu_crc))

        if self._axiom.u31.is_usage_present_on_device(0x93):
            print("  u93 Profiles CRC        : 0x{:08X}".format(self.reg_u93_profiles_cdu_crc))

        if self._axiom.u31.is_usage_present_on_device(0x94):
            print("  u94 Delta Scale Map CRC : 0x{:08X}".format(self.reg_u94_delta_scale_map_cdu_crc))
        print("  Runtime Hash            : 0x{:08X}".format(self.reg_runtime_hash))

    # endregion

    # region u33 Usage Name Usage Revision 3
    def _init_registers_uifrev3(self):
        self.reg_runtime_crc = 0
        self.reg_runtime_nvm_crc = 0
        self.reg_bootloader_crc = 0
        self.reg_nvltl_usage_config_crc = 0
        self.reg_vltl_usage_config_crc = 0
        self.reg_u22_sequence_data_cdu_crc = 0
        self.reg_u43_hotspots_cdu_crc = 0
        self.reg_u77_dod_calibration_data_crc = 0
        self.reg_u93_profiles_cdu_crc = 0
        self.reg_u94_delta_scale_map_cdu_crc = 0
        self.reg_runtime_hash = 0

    def _unpack_uifrev3(self):
        (rt_crc, rt_nvm_crc, bl_crc, nvltl_config_crc, vltl_config_crc, u22_crc, u43_crc, u77_crc, u93_crc, u94_crc,
         hash) = struct.unpack(
            "<11I", bytes(bytearray(self._usage_binary_data[0:44])))
        self.reg_runtime_crc = rt_crc
        self.reg_runtime_nvm_crc = rt_nvm_crc
        self.reg_bootloader_crc = bl_crc
        self.reg_nvltl_usage_config_crc = nvltl_config_crc
        self.reg_vltl_usage_config_crc = vltl_config_crc
        self.reg_u22_sequence_data_cdu_crc = u22_crc
        self.reg_u43_hotspots_cdu_crc = u43_crc
        self.reg_u77_dod_calibration_data_crc = u77_crc
        self.reg_u93_profiles_cdu_crc = u93_crc
        self.reg_u94_delta_scale_map_cdu_crc = u94_crc
        self.reg_runtime_hash = hash

    def _print_registers_uifrev3(self):
        print("u33 CRC Data")
        print("  Runtime CRC                  : 0x{:08X}".format(self.reg_runtime_crc))
        print("  Runtime NVM CRC              : 0x{:08X}".format(self.reg_runtime_nvm_crc))
        print("  Bootloader CRC               : 0x{:08X}".format(self.reg_bootloader_crc))
        print("  NVM Usage Config CRC         : 0x{:08X}".format(self.reg_nvltl_usage_config_crc))
        print("  RAM Usage Config CRC         : 0x{:08X}".format(self.reg_vltl_usage_config_crc))

        if self._axiom.u31.is_usage_present_on_device(0x22):
            print("  u22 Sequence Data CRC        : 0x{:08X}".format(self.reg_u22_sequence_data_cdu_crc))

        if self._axiom.u31.is_usage_present_on_device(0x43):
            print("  u43 Hotspots CRC             : 0x{:08X}".format(self.reg_u43_hotspots_cdu_crc))

        if self._axiom.u31.is_usage_present_on_device(0x77):
            print("  u77 DoD Calibration Data CRC : 0x{:08X}".format(self.reg_u77_dod_calibration_data_crc))

        if self._axiom.u31.is_usage_present_on_device(0x93):
            print("  u93 Profiles CRC             : 0x{:08X}".format(self.reg_u93_profiles_cdu_crc))

        if self._axiom.u31.is_usage_present_on_device(0x94):
            print("  u94 Delta Scale Map CRC      : 0x{:08X}".format(self.reg_u94_delta_scale_map_cdu_crc))
        print("  Runtime Hash                 : 0x{:08X}".format(self.reg_runtime_hash))
# endregion
