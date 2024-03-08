# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import struct
from time import sleep


class u48_GPIOControls:
    USAGE_ID = 0x48

    def __init__(self, axiom, read=True):
        self._axiom = axiom

        # Get the usage number from the axiom class
        self._usage_revision = self._axiom.get_usage_revision(self.USAGE_ID)

        # Initialise a buffer for the usage's contents to be read into and unpacked/packed
        self._usage_binary_data = [0] * self._axiom.get_usage_length(self.USAGE_ID)

        # To handle different usage revisions, there are different methods that handle
        # register initialisation (in this python class)
        # Use the getattr() find find the appropriate methods that pertain the usage revision.
        self._init_registers = getattr(self, "_init_registers_uifrev{}".format(self._usage_revision), None)

        # Raise an exception if an unsupported version of the usage is found.
        if self._init_registers is None:
            raise Exception(
                "Unsupported revision of {}. Revision: {}".format(self.__class__.__name__, self._usage_revision))

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
        if write_to_nvm:
            self._axiom.system_manager_command(self._axiom.SYSMGR_CMD_STOP)

        self._axiom.config_write_usage_to_device(self.USAGE_ID, self._usage_binary_data)

        if write_to_nvm:
            self._axiom.system_manager_command(self._axiom.SYSMGR_CMD_SAVE_CONFIG)
            sleep(0.1)

        self.read()

    def print(self):
        print("u48 GPIO Controls")
        for pins in range(len(self.reg_gpio_pins)):
            gpio_functions_lookup = {value: key for key, value in self.gpio_functions[pins].items()}
            print("GPIO %u: %s" % (pins, gpio_functions_lookup[self.reg_gpio_pins[pins]]))

    def _unpack(self):
        self.reg_gpio_pins[0:len(self.reg_gpio_pins)] = struct.unpack(("<%uB" % len(self.reg_gpio_pins)), bytes(
            bytearray(self._usage_binary_data[0:len(self.reg_gpio_pins)])))

    def _pack(self):
        # Convert the usage binary data into a byte array for struct pack to work
        usage_as_bytearray = bytearray(self._usage_binary_data)

        # pack 5 unsigned chars (bytes) into 'usage_as_bytearray' starting at offset 0
        struct.pack_into(("<%uB" % len(self.reg_gpio_pins)), usage_as_bytearray, 0, *self.reg_gpio_pins)
        # if there were more options after this, would start at offset 40 (5 lots of 8-bit values have already been packed in)

        # Convert the binary usage data into a list
        self._usage_binary_data = list(usage_as_bytearray)

    # region u48 Specific Methods
    # there are no u48 specific methods
    # endregion

    # region u48 GPIO Controls Usage Revision 7: AX112A
    def _init_registers_uifrev7(self):
        # A list of registers supported by this usage revision
        self.reg_gpio_pins = [0] * 5
        self.gpio_functions = [0] * 5

        self.gpio_functions[0] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, OUTPUT_AE_GPIO_1=8, SELF_TEST_BUSY=11,
                                      SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14, AE_CLIPPING=16)
        self.gpio_functions[1] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, HSYNC=8, OUTPUT_AE_GPIO_0=9,
                                      SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14,
                                      AE_CLIPPING=16)
        self.gpio_functions[2] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, VSYNC_EXTSYNC=8, OUTPUT_AE_GPIO_1=9,
                                      SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14,
                                      AE_CLIPPING=16)
        self.gpio_functions[3] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, OUTPUT_UART_TX=8, OUTPUT_AE_GPIO_0=9,
                                      SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14,
                                      AE_CLIPPING=16)
        self.gpio_functions[4] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, OUTPUT_UART_TX=8, OUTPUT_AE_GPIO_1=9,
                                      SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14,
                                      AE_CLIPPING=16)

    # endregion

    # region u48 GPIO Controls Usage Revision 8: AX54A, AX80A
    def _init_registers_uifrev8(self):
        # A list of registers supported by this usage revision
        self.reg_gpio_pins = [0] * 3
        self.gpio_functions = [0] * 3

        self.gpio_functions[0] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, HSYNC=8, OUTPUT_AE_GPIO_0=9,
                                      SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14,
                                      AE_CLIPPING=16)
        self.gpio_functions[1] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, VSYNC_EXTSYNC=8, OUTPUT_AE_GPIO_1=9,
                                      SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14,
                                      AE_CLIPPING=16)
        self.gpio_functions[2] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, OUTPUT_UART_TX=8, OUTPUT_AE_GPIO_1=9,
                                      SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14,
                                      AE_CLIPPING=16)

    # endregion

    # region u48 GPIO Controls Usage Revision 9: AX198A

    def _init_registers_uifrev9(self):
        # A list of registers supported by this usage revision
        self.reg_gpio_pins = [0] * 5
        self.gpio_functions = [0] * 5

        self.gpio_functions[0] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, OUTPUT_AE_GPIO_1=8, SELF_TEST_BUSY=11,
                                      SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14, AE_CLIPPING=16)
        self.gpio_functions[1] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, HSYNC=8, OUTPUT_AE_GPIO_0=9,
                                      SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14,
                                      AE_CLIPPING=16)
        self.gpio_functions[2] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, VSYNC_EXTSYNC=8, OUTPUT_AE_GPIO_1=9,
                                      SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13, HOVER_PROX=14,
                                      AE_CLIPPING=16)
        self.gpio_functions[3] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, OUTPUT_UART_TX=8, VSYNC_EXTSYNC=9,
                                      OUTPUT_AE_GPIO_0=10, SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13,
                                      HOVER_PROX=14, AE_CLIPPING=16)
        self.gpio_functions[4] = dict(LOW=0, HIGH=1, INPUT_PULLUP=3, INPUT_HIZ=4, OUTPUT_UART_TX=8, VSYNC_EXTSYNC=9,
                                      OUTPUT_AE_GPIO_1=10, SELF_TEST_BUSY=11, SELF_TEST_STATUS=12, HEARTBEAT=13,
                                      HOVER_PROX=14, AE_CLIPPING=16)
# endregion
