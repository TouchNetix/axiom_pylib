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

import spidev
from time              import sleep

class SPI_Comms:
    def __init__(self, bus, device):
        self.__spi = spidev.SpiDev()
        self.__spi.open(bus, device)

        # Configure SPI bus, less than 7MHz will work
        self.__spi.max_speed_hz = 7000000
        self.__spi.mode = 0

    def comms_init(self, axiom):
        self.__axiom = axiom

    def read_page(self, target_address, length):
        ta_msb = (target_address & 0xFF00) >> 8
        ta_lsb = (target_address & 0x00FF)

        length_msb = (length & 0x7F00) >> 8
        length_lsb = (length & 0x00FF)

        length_msb |= 0x80 # Set the READ bit

        spi_header  = [ta_lsb, ta_msb, length_lsb, length_msb]
        spi_padding = [0x00] * 32
        spi_body    = [0x00] * length
        spi_op      = spi_header + spi_padding + spi_body
        self.__spi.xfer(spi_op)
        sleep(0.001)
        return spi_op[36:]


    def write_page(self, target_address, length, payload):
        if length > len(payload):
            print("ERROR: Asked to write more bytes than available in payload: ")
            print("Length: %d, and given payload is %d" % (length,len(payload)))
            raise AssertionError

        ta_msb = (target_address & 0xFF00) >> 8
        ta_lsb = (target_address & 0x00FF)

        length_msb = (length & 0x7F00) >> 8
        length_lsb = (length & 0x00FF)

        length_msb &= ~0x80 # Ensure the read bit is clear

        spi_header  = [ta_lsb, ta_msb, length_lsb, length_msb]
        spi_padding = [0x00] * 32
        spi_body    = payload
        spi_op      = spi_header + spi_padding + spi_body
        self.__spi.xfer(spi_op)
        sleep(0.001)


    def close(self):
        self.__spi.close()
