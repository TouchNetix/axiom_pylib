################################################################################
#                                    NOTICE
#
# Copyright (c) 2010 - 2023 TouchNetix Limited
# ALL RIGHTS RESERVED.
#
# The source  code contained  or described herein  and all documents  related to
# the source code ("Material") are owned by TouchNetix Limited ("TouchNetix") or
# its suppliers  or licensors. Title to the Material  remains with TouchNetix or
# its   suppliers  and  licensors. The  Material  contains  trade  secrets   and
# proprietary  and confidential information  of TouchNetix or its  suppliers and
# licensors.  The  Material  is  protected  by  worldwide  copyright  and  trade
# secret  laws and  treaty  provisions.  No part  of the Material  may be  used,
# copied,  reproduced,  modified,   published,  uploaded,  posted,  transmitted,
# distributed or disclosed in any way without TouchNetix's prior express written
# permission.
#
# No  license under any  patent, copyright,  trade secret or other  intellectual
# property  right is granted to or conferred upon you by disclosure or  delivery
# of  the Materials, either  expressly, by implication, inducement, estoppel  or
# otherwise.  Any  license  under  such  intellectual  property rights  must  be
# expressly approved by TouchNetix in writing.
#
################################################################################

import struct
from time import sleep

class u33_CRCData:
    USAGE_ID = 0x33

    def __init__(self, axiom, read = True):
        self._axiom = axiom

        # Get the usage number from the axiom class
        self._usage_revision = self._axiom.get_usage_revision(self.USAGE_ID)

        # Initialise a buffer for the usage's contents to be read into and unpacked/packed
        self._usage_binary_data = [0] * self._axiom.get_usage_length(self.USAGE_ID)

        # To handle different usage revisions, there are different methods that handle
        # register initialisation (in this python class), dumping out the contents of
        # a usage and unpacking and packing the usage's variables back into binary formats.
        # Use the getattr() find find the appropiate methods that pertain the usage revision.
        self._init_registers   = getattr(self, "_init_registers_uifrev{}".format( self._usage_revision), None)
        self._print_registers  = getattr(self, "_print_registers_uifrev{}".format(self._usage_revision), None)
        self._unpack_registers = getattr(self, "_unpack_uifrev{}".format(         self._usage_revision), None)

        # Raise an exception if an unsupported version of the usage is found.
        if (self._init_registers   is None or 
            self._print_registers  is None or 
            self._unpack_registers is None):
            raise Exception("Unsupported revision of {}. Revision: {}".format(self.__class__.__name__, self._usage_revision))

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

    def write(self, write_to_nvm=False):
        self._pack()
        if write_to_nvm == True:
            self._axiom.system_manager_command(self._axiom.SYSMGR_CMD_STOP)

        self._axiom.config_write_usage_to_device(self.USAGE_ID, self._usage_binary_data)

        if write_to_nvm == True:
            self._axiom.system_manager_command(self._axiom.SYSMGR_CMD_SAVE_CONFIG)
            sleep(0.1)
        
        self.read()

    def print(self):
        self._print_registers()

    def _unpack(self):
        self._unpack_registers()

#region u33 Specific Methods
    def compare_u33(self, other_u33, print_results = False):
        config_nvm_crc_check = True if self.reg_nvltl_usage_config_crc      == other_u33.reg_nvltl_usage_config_crc else False
        config_ram_crc_check = True if self.reg_vltl_usage_config_crc       == other_u33.reg_vltl_usage_config_crc else False
        config_u22_crc_check = True if self.reg_u22_sequence_data_cdu_crc   == other_u33.reg_u22_sequence_data_cdu_crc else False
        config_u43_crc_check = True if self.reg_u43_hotspots_cdu_crc        == other_u33.reg_u43_hotspots_cdu_crc else False
        config_u93_crc_check = True if self.reg_u93_profiles_cdu_crc        == other_u33.reg_u93_profiles_cdu_crc else False
        config_u94_crc_check = True if self.reg_u94_delta_scale_map_cdu_crc == other_u33.reg_u94_delta_scale_map_cdu_crc else False

        if print_results:
            print("u33 Comparison            %10s - %10s" % ("Device".center(10), "File".center(10)))
            print("NVM Usage Config CRC    : 0x%08X - 0x%08X - %s" % (self.reg_nvltl_usage_config_crc,      other_u33.reg_nvltl_usage_config_crc,      "OK" if config_nvm_crc_check else "MISMATCHED"))
            print("RAM Usage Config CRC    : 0x%08X - 0x%08X - %s" % (self.reg_vltl_usage_config_crc,       other_u33.reg_vltl_usage_config_crc,       "OK" if config_ram_crc_check else "MISMATCHED"))
            print("u22 Sequence Data CRC   : 0x%08X - 0x%08X - %s" % (self.reg_u22_sequence_data_cdu_crc,   other_u33.reg_u22_sequence_data_cdu_crc,   "OK" if config_u22_crc_check else "MISMATCHED"))
            print("u43 Hotspots CRC        : 0x%08X - 0x%08X - %s" % (self.reg_u43_hotspots_cdu_crc,        other_u33.reg_u43_hotspots_cdu_crc,        "OK" if config_u43_crc_check else "MISMATCHED"))
            print("u93 Profiles CRC        : 0x%08X - 0x%08X - %s" % (self.reg_u93_profiles_cdu_crc,        other_u33.reg_u93_profiles_cdu_crc,        "OK" if config_u93_crc_check else "MISMATCHED"))
            print("u94 Delta Scale Map CRC : 0x%08X - 0x%08X - %s" % (self.reg_u94_delta_scale_map_cdu_crc, other_u33.reg_u94_delta_scale_map_cdu_crc, "OK" if config_u94_crc_check else "MISMATCHED"))

        if (config_nvm_crc_check and
            config_ram_crc_check and
            config_u22_crc_check and
            config_u43_crc_check and
            config_u93_crc_check and
            config_u94_crc_check):
            return True
        else:
            return False
#endregion

#region uXX Usage Name Usage Revision 2
    def _init_registers_uifrev2(self):
        self.reg_runtime_crc                 = 0
        self.reg_runtime_nvm_crc             = 0
        self.reg_bootloader_crc              = 0
        self.reg_nvltl_usage_config_crc      = 0
        self.reg_vltl_usage_config_crc       = 0
        self.reg_u22_sequence_data_cdu_crc   = 0
        self.reg_u43_hotspots_cdu_crc        = 0
        self.reg_u93_profiles_cdu_crc        = 0
        self.reg_u94_delta_scale_map_cdu_crc = 0
        self.reg_runtime_hash                = 0

    def _unpack_uifrev2(self):
        rt_crc, rt_nvm_crc, bl_crc, nvltl_config_crc, vltl_config_crc, u22_crc, u43_crc, u93_crc, u94_crc, hash = struct.unpack("<10I", bytes(bytearray(self._usage_binary_data[0:40])))
        self.reg_runtime_crc                 = rt_crc
        self.reg_runtime_nvm_crc             = rt_nvm_crc
        self.reg_bootloader_crc              = bl_crc
        self.reg_nvltl_usage_config_crc      = nvltl_config_crc
        self.reg_vltl_usage_config_crc       = vltl_config_crc
        self.reg_u22_sequence_data_cdu_crc   = u22_crc
        self.reg_u43_hotspots_cdu_crc        = u43_crc
        self.reg_u93_profiles_cdu_crc        = u93_crc
        self.reg_u94_delta_scale_map_cdu_crc = u94_crc
        self.reg_runtime_hash                = hash

    def _print_registers_uifrev2(self):
        print("u33 CRC Data")
        print("  Runtime CRC             : 0x{:08X}".format(self.reg_runtime_crc))
        print("  Runtime NVM CRC         : 0x{:08X}".format(self.reg_runtime_nvm_crc))
        print("  Bootloader CRC          : 0x{:08X}".format(self.reg_bootloader_crc))
        print("  NVM Usage Config CRC    : 0x{:08X}".format(self.reg_nvltl_usage_config_crc))
        print("  RAM Usage Config CRC    : 0x{:08X}".format(self.reg_vltl_usage_config_crc))
        print("  u22 Sequence Data CRC   : 0x{:08X}".format(self.reg_u22_sequence_data_cdu_crc))
        print("  u43 Hotspots CRC        : 0x{:08X}".format(self.reg_u43_hotspots_cdu_crc))
        print("  u93 Profiles CRC        : 0x{:08X}".format(self.reg_u93_profiles_cdu_crc))
        print("  u94 Delta Scale Map CRC : 0x{:08X}".format(self.reg_u94_delta_scale_map_cdu_crc))
        print("  Runtime Hash            : 0x{:08X}".format(self.reg_runtime_hash))
#endregion
