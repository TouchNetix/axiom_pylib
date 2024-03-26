# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import struct


class u32_DeviceCapabilities:
    USAGE_ID = 0x32

    def __init__(self, axiom, read=True):
        self._axiom = axiom

        # Get the usage number from the axiom class
        self._usage_revision = self._axiom.get_usage_revision(self.USAGE_ID)

        # Initialise a buffer for the usage's contents to be read into and unpacked/packed
        self._usage_binary_data = [0] * self._axiom.get_usage_length(self.USAGE_ID)

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
        raise Exception("Cannot write to u33. u33 is a read-only usage.")

    def print(self):
        self._print_registers()

    def _unpack(self):
        self._unpack_registers()

    # region u33 Specific Methods
    # endregion

    # region uXX Usage Name Usage Revision 1
    def _init_registers_uifrev1(self):
        self.reg_max_cts_nodes = 0
        self.reg_num_cts_channels = 0
        self.reg_num_aux_channels = 0
        self.reg_num_cts_driven_traces = 0
        self.reg_num_aux_driven_traces = 0
        self.reg_num_a_channels = 0
        self.reg_num_b_channels = 0
        self.reg_num_c_channels = 0
        self.reg_num_d_channels = 0
        self.reg_num_e_channels = 0
        self.reg_num_f_channels = 0
        self.reg_max_map_lengthbytes = 0
        self.reg_max_baseline_length_bytes = 0
        self.reg_num_baselines = 0
        self.reg_slave_i2c_supported = 0
        self.reg_slave_spi_supported = 0
        self.reg_slave_lin_supported = 0
        self.reg_slave_usb_supported = 0
        self.reg_slave_uart_supported = 0
        self.reg_irq_notify_supported = 0
        self.reg_external_sync_supported = 0
        self.reg_master_i2c_supported = 0
        self.reg_master_spi_supported = 0
        self.reg_master_gpio_supported = 0
        self.reg_num_user_gpios = 0
        self.reg_khz_to_jump_thousandths = 0

    def _unpack_uifrev1(self):
        # field0 = struct.unpack("<H", bytes(bytearray(self._usage_binary_data[0:2])))
        # self.reg_0 = (field0 & 0x0001)
        max_cts_nodes, num_cts_channels, num_aux_channels, \
            num_cts_driven_traces, num_aux_driven_traces, num_a_channels, num_b_channels, \
            num_c_channels, num_d_channels, num_e_channels, num_f_channels, max_map_lengthbytes, \
            max_baseline_length_bytes, num_baselines, _, interfaces, khz_to_jump_thousands = struct.unpack(
                "<H10B2H2BHI", bytes(bytearray(self._usage_binary_data[0:24])))

        self.reg_max_cts_nodes = max_cts_nodes
        self.reg_num_cts_channels = num_cts_channels
        self.reg_num_aux_channels = num_aux_channels
        self.reg_num_cts_driven_traces = num_cts_driven_traces
        self.reg_num_aux_driven_traces = num_aux_driven_traces
        self.reg_num_a_channels = num_a_channels
        self.reg_num_b_channels = num_b_channels
        self.reg_num_c_channels = num_c_channels
        self.reg_num_d_channels = num_d_channels
        self.reg_num_e_channels = num_e_channels
        self.reg_num_f_channels = num_f_channels
        self.reg_max_map_lengthbytes = max_map_lengthbytes
        self.reg_max_baseline_length_bytes = max_baseline_length_bytes
        self.reg_num_baselines = num_baselines

        self.reg_slave_i2c_supported = (interfaces & 0x0001) >> 0
        self.reg_slave_spi_supported = (interfaces & 0x0002) >> 1
        self.reg_slave_lin_supported = (interfaces & 0x0004) >> 2
        self.reg_slave_usb_supported = (interfaces & 0x0008) >> 3
        self.reg_slave_uart_supported = (interfaces & 0x0010) >> 4
        self.reg_irq_notify_supported = (interfaces & 0x0020) >> 5
        self.reg_external_sync_supported = (interfaces & 0x0040) >> 6
        self.reg_master_i2c_supported = (interfaces & 0x0080) >> 7
        self.reg_master_spi_supported = (interfaces & 0x0100) >> 8
        self.reg_master_gpio_supported = (interfaces & 0x0200) >> 9
        self.reg_num_user_gpios = (interfaces & 0xF000) >> 12

        self.reg_khz_to_jump_thousandths = khz_to_jump_thousands

    def _print_registers_uifrev1(self):
        print("u32 Device Capabilities")
        print("  Max CTS Nodes         : %u" % self.reg_max_cts_nodes)
        print("  Num CTS Channels      : %u" % self.reg_num_cts_channels)
        print("  Num AUX Channels      : %u" % self.reg_num_aux_channels)
        print("  Num CTS Driven Traces : %u" % self.reg_num_cts_driven_traces)
        print("  Num AUX Driven Traces : %u" % self.reg_num_aux_driven_traces)
        print("  Num A Channels        : %u" % self.reg_num_a_channels)
        print("  Num B Channels        : %u" % self.reg_num_b_channels)
        print("  Num C Channels        : %u" % self.reg_num_c_channels)
        print("  Num D Channels        : %u" % self.reg_num_d_channels)
        print("  Num E Channels        : %u" % self.reg_num_e_channels)
        print("  Num F Channels        : %u" % self.reg_num_f_channels)
        print("  Max Map Length        : %u bytes" % self.reg_max_map_lengthbytes)
        print("  Max Baseline Length   : %u bytes" % self.reg_max_baseline_length_bytes)
        print("  Num Baselines         : %u" % self.reg_num_baselines)

        print("  Slave I2C             : %sSupported" % ("" if self.reg_slave_i2c_supported == 1 else "Not "))
        print("  Slave SPI             : %sSupported" % ("" if self.reg_slave_spi_supported == 1 else "Not "))
        print("  Slave LIN             : %sSupported" % ("" if self.reg_slave_lin_supported == 1 else "Not "))
        print("  Slave USB             : %sSupported" % ("" if self.reg_slave_usb_supported == 1 else "Not "))
        print("  Slave UART            : %sSupported" % ("" if self.reg_slave_uart_supported == 1 else "Not "))
        print("  IRQ Notify            : %sSupported" % ("" if self.reg_irq_notify_supported == 1 else "Not "))
        print("  External Sync         : %sSupported" % ("" if self.reg_external_sync_supported == 1 else "Not "))
        print("  Master I2C            : %sSupported" % ("" if self.reg_master_i2c_supported == 1 else "Not "))
        print("  Master SPI            : %sSupported" % ("" if self.reg_master_spi_supported == 1 else "Not "))
        print("  Master GPIO           : %sSupported" % ("" if self.reg_master_gpio_supported == 1 else "Not "))
        print("  Num User GPIOs        : %u" % self.reg_num_user_gpios)

        print("  KHz to Jump           : %u (thousands)" % self.reg_khz_to_jump_thousandths)
# endregion
