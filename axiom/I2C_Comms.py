################################################################################
#                                    NOTICE
#
# Copyright (c) 2010 - 2020 TouchNetix Limited
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

from smbus2 import SMBus, i2c_msg

class I2C_Comms:
    def __init__(self, bus, address):
        self.__addr = address
        self.__bus = SMBus(bus)

    def comms_init(self, axiom):
        self.__axiom = axiom

    def read_page(self, target_address, length):
        ta_msb = (target_address & 0xFF00) >> 8
        ta_lsb = (target_address & 0x00FF)

        length_msb = (length & 0x7F00) >> 8
        length_lsb = (length & 0x00FF)

        length_msb |= 0x80 # Set the READ bit

        wr = i2c_msg.write(self.__addr, [ta_lsb, ta_msb, length_lsb, length_msb])
        rd = i2c_msg.read(self.__addr, length)

        try:
            self.__bus.i2c_rdwr(wr, rd)
        except IOError:
            pass # Silently handle IOError. You see this when attempting to enter bootloader mode

        return list(rd)


    def write_page(self, target_address, length, payload):
        ta_msb = (target_address & 0xFF00) >> 8
        ta_lsb = (target_address & 0x00FF)

        length_msb = (length & 0x7F00) >> 8
        length_lsb = (length & 0x00FF)

        length_msb &= ~0x80 # Ensure the read bit is clear

        write_header = [ta_lsb, ta_msb, length_lsb, length_msb]
        write_payload = payload
        write = write_header + write_payload

        wr = i2c_msg.write(self.__addr, write)
        self.__bus.i2c_rdwr(wr)

    def close(self):
        self.__bus.close()