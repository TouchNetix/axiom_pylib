# Copyright (c) 2024 TouchNetix
# 
# This file is part of [Project Name] and is released under the MIT License: 
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

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