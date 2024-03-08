# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import struct
from time import sleep


class u06_SelfTest:
    USAGE_ID = 0x06

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
        self._pack_registers = getattr(self, "_pack_uifrev{}".format(self._usage_revision), None)

        # Raise an exception if an unsupported version of the usage is found.
        if (self._init_registers is None or
                self._print_registers is None or
                self._unpack_registers is None or
                self._pack_registers is None):
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
            self._axiom.u02.send_command(self._axiom.u02.CMD_STOP)

        self._axiom.config_write_usage_to_device(self.USAGE_ID, self._usage_binary_data)

        if write_to_nvm:
            self._axiom.u02.send_command(self._axiom.u02.CMD_SAVE_CONFIG)
            sleep(0.1)

        self.read()

    def print(self):
        self._print_registers()

    def _unpack(self):
        self._unpack_registers()

    def _pack(self):
        self._pack_registers()

    # region u06 Self Test Usage Revision 3
    def _init_registers_uifrev3(self):
        self.reg_enable_self_test_on_boot = 0
        self.reg_enable_self_test_on_heartbeat = 0
        self.reg_stop_tests_on_first_error = 0
        self.reg_enable_u83_self_test_frames = 0
        self.reg_u83_self_test_every_n_frames = 0
        self.reg_u83_self_test_jump = 0
        self.reg_aux_channels_use_calibration_capacitors = 0
        self.reg_run_test_n_on_boot = 0
        self.reg_run_test_n_on_heartbeat = 0
        self.reg_run_test_n_on_host_trigger = 0

        self.reg_self_test_5_sense_pins_pin_sense_mask = [0] * 16
        self.reg_self_test_5_sense_pins_gross_leakage_limit = 0
        self.reg_self_test_5_sense_pins_marginal_leakage_limit = 0
        self.reg_self_test_5_sense_pins_shield_gross_leakage_limit = 0
        self.reg_self_test_5_sense_pins_shield_marginal_leakage_limit = 0

        self.reg_self_test_6_trans_middle_limits_node_max = 0
        self.reg_self_test_6_trans_middle_limits_node_min = 0
        self.reg_self_test_6_trans_middle_limits_average_max = 0
        self.reg_self_test_6_trans_middle_limits_average_min = 0
        self.reg_self_test_6_trans_middle_limits_peak2peak_max = 0
        self.reg_self_test_6_trans_edge_limits_node_max = 0
        self.reg_self_test_6_trans_edge_limits_node_min = 0
        self.reg_self_test_6_trans_edge_limits_average_max = 0
        self.reg_self_test_6_trans_edge_limits_average_min = 0
        self.reg_self_test_6_trans_corner_limits_node_max = 0
        self.reg_self_test_6_trans_corner_limits_node_min = 0

        self.reg_self_test_7_abs_rows_limits_chan_max = 0
        self.reg_self_test_7_abs_rows_limits_chan_min = 0
        self.reg_self_test_7_abs_rows_limits_average_max = 0
        self.reg_self_test_7_abs_rows_limits_average_min = 0
        self.reg_self_test_7_abs_cols_limits_chan_max = 0
        self.reg_self_test_7_abs_cols_limits_chan_min = 0
        self.reg_self_test_7_abs_cols_limits_average_max = 0
        self.reg_self_test_7_abs_cols_limits_average_min = 0

        self.reg_self_test_8_aux_limits_chan_n_chan_max = [0] * 4
        self.reg_self_test_8_aux_limits_chan_n_chan_min = [0] * 4

    def _unpack_uifrev3(self):
        field0, field1, field2, field3 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[0:8])))
        self.reg_enable_self_test_on_boot = (field0 & 0x0001)
        self.reg_enable_self_test_on_heartbeat = (field0 & 0x0002) >> 1
        self.reg_stop_tests_on_first_error = (field1 & 0x0001)
        self.reg_enable_u83_self_test_frames = (field1 & 0x0002) >> 1
        self.reg_u83_self_test_every_n_frames = (field1 & 0xFFF0) >> 4
        self.reg_u83_self_test_jump = field2
        self.reg_aux_channels_use_calibration_capacitors = (field3 & 0x0001)

        field0, field1, field2 = struct.unpack("<3H", bytes(bytearray(self._usage_binary_data[8:14])))
        self.reg_run_test_n_on_boot = field0
        self.reg_run_test_n_on_heartbeat = field1
        self.reg_run_test_n_on_host_trigger = field2

        field = struct.unpack("<16H", bytes(bytearray(self._usage_binary_data[14:46])))
        self.reg_self_test_5_sense_pins_pin_sense_mask = [*field, ]  # Convert tuple to list

        field0, field1, field2, field3 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[46:54])))
        self.reg_self_test_5_sense_pins_gross_leakage_limit = field0
        self.reg_self_test_5_sense_pins_marginal_leakage_limit = field1
        self.reg_self_test_5_sense_pins_shield_gross_leakage_limit = field2
        self.reg_self_test_5_sense_pins_shield_marginal_leakage_limit = field3

        field0, field1, field2, field3, field4 = struct.unpack("<5H", bytes(bytearray(self._usage_binary_data[54:64])))
        self.reg_self_test_6_trans_middle_limits_node_max = field0
        self.reg_self_test_6_trans_middle_limits_node_min = field1
        self.reg_self_test_6_trans_middle_limits_average_max = field2
        self.reg_self_test_6_trans_middle_limits_average_min = field3
        self.reg_self_test_6_trans_middle_limits_peak2peak_max = field4

        field0, field1, field2, field3, _ = struct.unpack("<5H", bytes(bytearray(self._usage_binary_data[64:74])))
        self.reg_self_test_6_trans_edges_limits_node_max = field0
        self.reg_self_test_6_trans_edges_limits_node_min = field1
        self.reg_self_test_6_trans_edges_limits_average_max = field2
        self.reg_self_test_6_trans_edges_limits_average_min = field3

        field0, field1, _, _, _ = struct.unpack("<5H", bytes(bytearray(self._usage_binary_data[74:84])))
        self.reg_self_test_6_trans_corners_limits_node_max = field0
        self.reg_self_test_6_trans_corners_limits_node_min = field1

        field0, field1, field2, field3 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[84:92])))
        self.reg_self_test_7_abs_rows_limits_chan_max = field0
        self.reg_self_test_7_abs_rows_limits_chan_min = field1
        self.reg_self_test_7_abs_rows_limits_average_max = field2
        self.reg_self_test_7_abs_rows_limits_average_min = field3

        field0, field1, field2, field3 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[92:100])))
        self.reg_self_test_7_abs_cols_limits_chan_max = field0
        self.reg_self_test_7_abs_cols_limits_chan_min = field1
        self.reg_self_test_7_abs_cols_limits_average_max = field2
        self.reg_self_test_7_abs_cols_limits_average_min = field3

        field0, field1, field2, field3, field4, field5, field6, field7 = struct.unpack("<8H", bytes(
            bytearray(self._usage_binary_data[100:116])))
        self.reg_self_test_8_aux_limits_chan_n_chan_max[0] = field0
        self.reg_self_test_8_aux_limits_chan_n_chan_min[0] = field1
        self.reg_self_test_8_aux_limits_chan_n_chan_max[1] = field2
        self.reg_self_test_8_aux_limits_chan_n_chan_min[1] = field3
        self.reg_self_test_8_aux_limits_chan_n_chan_max[2] = field4
        self.reg_self_test_8_aux_limits_chan_n_chan_min[2] = field5
        self.reg_self_test_8_aux_limits_chan_n_chan_max[3] = field6
        self.reg_self_test_8_aux_limits_chan_n_chan_min[3] = field7

    def _pack_uifrev3(self):
        # Convert the usage binary data into a byte array for struct pack to work
        usage_as_bytearray = bytearray(self._usage_binary_data)

        fields = [0] * 7
        fields[0] = (self.reg_enable_self_test_on_boot & 0x0001)
        fields[0] |= ((self.reg_enable_self_test_on_heartbeat << 1) & 0x0002)
        fields[1] = (self.reg_stop_tests_on_first_error & 0x0001)
        fields[1] |= ((self.reg_enable_u83_self_test_frames << 1) & 0x0002)
        fields[1] |= ((self.reg_u83_self_test_every_n_frames << 4) & 0xFFF0)
        fields[2] = (self.reg_u83_self_test_jump & 0xFFFF)
        fields[3] = (self.reg_aux_channels_use_calibration_capacitors & 0x0001)
        fields[4] = (self.reg_run_test_n_on_boot & 0xFFFF)
        fields[5] = (self.reg_run_test_n_on_heartbeat & 0xFFFF)
        fields[6] = (self.reg_run_test_n_on_host_trigger & 0xFFFF)
        struct.pack_into("<7H", usage_as_bytearray, 0, *fields)

        struct.pack_into("<16H", usage_as_bytearray, 14, *self.reg_self_test_5_sense_pins_pin_sense_mask)

        fields = [0] * 4
        fields[0] = (self.reg_self_test_5_sense_pins_gross_leakage_limit & 0xFFFF)
        fields[1] = (self.reg_self_test_5_sense_pins_marginal_leakage_limit & 0xFFFF)
        fields[2] = (self.reg_self_test_5_sense_pins_shield_gross_leakage_limit & 0xFFFF)
        fields[3] = (self.reg_self_test_5_sense_pins_shield_marginal_leakage_limit & 0xFFFF)
        struct.pack_into("<4H", usage_as_bytearray, 46, *fields)

        fields = [0] * 15
        fields[0] = (self.reg_self_test_6_trans_middle_limits_node_max & 0xFFFF)
        fields[1] = (self.reg_self_test_6_trans_middle_limits_node_min & 0xFFFF)
        fields[2] = (self.reg_self_test_6_trans_middle_limits_average_max & 0xFFFF)
        fields[3] = (self.reg_self_test_6_trans_middle_limits_average_min & 0xFFFF)
        fields[4] = (self.reg_self_test_6_trans_middle_limits_peak2peak_max & 0xFFFF)
        fields[5] = (self.reg_self_test_6_trans_edges_limits_node_max & 0xFFFF)
        fields[6] = (self.reg_self_test_6_trans_edges_limits_node_min & 0xFFFF)
        fields[7] = (self.reg_self_test_6_trans_edges_limits_average_max & 0xFFFF)
        fields[8] = (self.reg_self_test_6_trans_edges_limits_average_min & 0xFFFF)
        fields[9] = 0
        fields[10] = (self.reg_self_test_6_trans_corners_limits_node_max & 0xFFFF)
        fields[11] = (self.reg_self_test_6_trans_corners_limits_node_min & 0xFFFF)
        fields[12] = 0
        fields[13] = 0
        fields[14] = 0
        struct.pack_into("<15H", usage_as_bytearray, 54, *fields)

        fields = [0] * 8
        fields[0] = (self.reg_self_test_7_abs_rows_limits_chan_max & 0xFFFF)
        fields[1] = (self.reg_self_test_7_abs_rows_limits_chan_min & 0xFFFF)
        fields[2] = (self.reg_self_test_7_abs_rows_limits_average_max & 0xFFFF)
        fields[3] = (self.reg_self_test_7_abs_rows_limits_average_min & 0xFFFF)
        fields[4] = (self.reg_self_test_7_abs_cols_limits_chan_max & 0xFFFF)
        fields[5] = (self.reg_self_test_7_abs_cols_limits_chan_min & 0xFFFF)
        fields[6] = (self.reg_self_test_7_abs_cols_limits_average_max & 0xFFFF)
        fields[7] = (self.reg_self_test_7_abs_cols_limits_average_min & 0xFFFF)
        struct.pack_into("<8H", usage_as_bytearray, 84, *fields)

        fields = [0] * 8
        fields[0] = ((self.reg_self_test_8_aux_limits_chan_n_chan_max[0]) & 0xFFFF)
        fields[1] = ((self.reg_self_test_8_aux_limits_chan_n_chan_min[0]) & 0xFFFF)
        fields[2] = ((self.reg_self_test_8_aux_limits_chan_n_chan_max[1]) & 0xFFFF)
        fields[3] = ((self.reg_self_test_8_aux_limits_chan_n_chan_min[1]) & 0xFFFF)
        fields[4] = ((self.reg_self_test_8_aux_limits_chan_n_chan_max[2]) & 0xFFFF)
        fields[5] = ((self.reg_self_test_8_aux_limits_chan_n_chan_min[2]) & 0xFFFF)
        fields[6] = ((self.reg_self_test_8_aux_limits_chan_n_chan_max[3]) & 0xFFFF)
        fields[7] = ((self.reg_self_test_8_aux_limits_chan_n_chan_min[3]) & 0xFFFF)
        struct.pack_into("<8H", usage_as_bytearray, 100, *fields)

        # Convert the binary usage data into a list
        self._usage_binary_data = list(usage_as_bytearray)

    def _print_registers_uifrev3(self):
        print("u06 Self Tests")
        print("  Enable Self Test on Boot          : %s" % ("Yes" if self.reg_enable_self_test_on_boot else "No"))
        print("  Enable Self Test on Heartbeat     : %s" % ("Yes" if self.reg_enable_self_test_on_heartbeat else "No"))
        print("")
        print("  Stop Self Tests on First Failure  : %s" % ("Yes" if self.reg_stop_tests_on_first_error else "No"))
        print("  Enable u83 Self Test Frames       : %s" % ("Yes" if self.reg_enable_u83_self_test_frames else "No"))
        print("  u83 Self Test Every               : %u frames" % self.reg_u83_self_test_every_n_frames)
        print("  u83 Self Test Jump                : %u jump" % self.reg_u83_self_test_jump)
        print("  AUX Channels Use Calibration Caps : %s" % (
            "Yes" if self.reg_aux_channels_use_calibration_capacitors else "No"))
        print("")
        print("  Run Tests on Boot                 : %04X" % self.reg_run_test_n_on_boot)
        print("  Run Tests on Heartbeat            : %04X" % self.reg_run_test_n_on_heartbeat)
        print("  Run Tests on Host Trigger         : %04X" % self.reg_run_test_n_on_host_trigger)
        print("")
        print("  Self Test 5 - Sense and Shield Pin Leakage")
        print("    Pin Mask")
        for i in range(len(self.reg_self_test_5_sense_pins_pin_sense_mask)):
            print("    Pin Mask[%2u] : %04X" % (i, self.reg_self_test_5_sense_pins_pin_sense_mask[i]))
        print("    Sense Gross Leakage Limit    : %5u" % self.reg_self_test_5_sense_pins_gross_leakage_limit)
        print("    Sense Marginal Leakage Limit : %5u" % self.reg_self_test_5_sense_pins_marginal_leakage_limit)
        print("    Shield Gross Leakage Limit   : %5u" % self.reg_self_test_5_sense_pins_shield_gross_leakage_limit)
        print("    Shield Margin Leakage Limit  : %5u" % self.reg_self_test_5_sense_pins_shield_marginal_leakage_limit)
        print("")
        print("  Self Test 6 - Trans Signal Limits")
        print("    Middle Nodes")
        print("      Node Max        : %5u" % self.reg_self_test_6_trans_middle_limits_node_max)
        print("      Node Min        : %5u" % self.reg_self_test_6_trans_middle_limits_node_min)
        print("      Average Max     : %5u" % self.reg_self_test_6_trans_middle_limits_average_max)
        print("      Average Min     : %5u" % self.reg_self_test_6_trans_middle_limits_average_min)
        print("      Peak 2 Peak Max : %5u" % self.reg_self_test_6_trans_middle_limits_peak2peak_max)
        print("    Edge Nodes")
        print("      Node Max        : %5u" % self.reg_self_test_6_trans_edges_limits_node_max)
        print("      Node Min        : %5u" % self.reg_self_test_6_trans_edges_limits_node_min)
        print("      Average Max     : %5u" % self.reg_self_test_6_trans_edges_limits_average_max)
        print("      Average Min     : %5u" % self.reg_self_test_6_trans_edges_limits_average_min)
        print("    Corner Nodes")
        print("      Node Max        : %5u" % self.reg_self_test_6_trans_corners_limits_node_max)
        print("      Node Min        : %5u" % self.reg_self_test_6_trans_corners_limits_node_min)
        print("")
        print("  Self Test 7 - ABS Signal Limits")
        print("    ABS Rows")
        print("      Channel Max : %5u" % self.reg_self_test_7_abs_rows_limits_chan_max)
        print("      Channel Min : %5u" % self.reg_self_test_7_abs_rows_limits_chan_min)
        print("      Average Max : %5u" % self.reg_self_test_7_abs_rows_limits_average_max)
        print("      Average Min : %5u" % self.reg_self_test_7_abs_rows_limits_average_min)
        print("    ABS Cols")
        print("      Channel Max : %5u" % self.reg_self_test_7_abs_cols_limits_chan_max)
        print("      Channel Min : %5u" % self.reg_self_test_7_abs_cols_limits_chan_min)
        print("      Average Max : %5u" % self.reg_self_test_7_abs_cols_limits_average_max)
        print("      Average Min : %5u" % self.reg_self_test_7_abs_cols_limits_average_min)
        print("")
        print("  Self Test 8 - AUX Signal Limits")
        print("          %5u %5u %5u %5u" % (0, 1, 2, 3))
        print("    Max : %5u %5u %5u %5u" % (
            self.reg_self_test_8_aux_limits_chan_n_chan_max[0], self.reg_self_test_8_aux_limits_chan_n_chan_max[1],
            self.reg_self_test_8_aux_limits_chan_n_chan_max[2], self.reg_self_test_8_aux_limits_chan_n_chan_max[3]))
        print("    Max : %5u %5u %5u %5u" % (
            self.reg_self_test_8_aux_limits_chan_n_chan_min[0], self.reg_self_test_8_aux_limits_chan_n_chan_min[1],
            self.reg_self_test_8_aux_limits_chan_n_chan_min[2], self.reg_self_test_8_aux_limits_chan_n_chan_min[3]))
# endregion
