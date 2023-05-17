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

class uXX_UsageName:
    USAGE_ID = 0xFF

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
        self._pack_registers   = getattr(self, "_pack_uifrev{}".format(           self._usage_revision), None)

        # Raise an exception if an unsupported version of the usage is found.
        if (self._init_registers   is None or 
            self._print_registers  is None or 
            self._unpack_registers is None or 
            self._pack_registers   is None):
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

    def write(self, write_to_nvm = False):
        self._pack()
        if write_to_nvm:
            self._axiom.system_manager_command(self._axiom.SYSMGR_CMD_STOP)

        self._axiom.config_write_usage_to_device(self.USAGE_ID, self._usage_binary_data)

        if write_to_nvm:
            self._axiom.system_manager_command(self._axiom.SYSMGR_CMD_SAVE_CONFIG)
            sleep(0.1)
        
        self.read()

    def print(self):
        self._print_registers()

    def _unpack(self):
        self._unpack_registers()

    def _pack(self):
        self._pack_registers()

#region uXX Specific Methods
#endregion

#region uXX Usage Name Usage Revision 1
    def _init_registers_uifrev1(self):
        # A list of registers supported by this usage revision
        self.reg_0 = 0

    def _unpack_uifrev1(self):
        field0 = struct.unpack("<H", bytes(bytearray(self._usage_binary_data[0:2])))
        self.reg_0 = (field0 & 0x0001)
        
    def _pack_uifrev1(self):
        # Convert the usage binary data into a byte array for struct pack to work
        usage_as_bytearray = bytearray(self._usage_binary_data)
        
        fields = [0] * 1
        fields[0] = ((self.reg_0) & 0x0001)
        struct.pack_into("<H", usage_as_bytearray, 0, *fields)

        # Convert the binary usage data into a list
        self._usage_binary_data = list(usage_as_bytearray)

    def _print_registers_uifrev1(self):
        print("uFF Usage Name")
        print("  Register 0 : %s" % ("On" if self.reg_0 else "Off"))
#endregion
