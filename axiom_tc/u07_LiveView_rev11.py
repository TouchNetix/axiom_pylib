# Copyright (c) 2025 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from .UsageRevisionBase import UsageRevisionBase
from . import u07_LiveView_Utils as u07_Utils
import struct

class u07_LiveViewRev11(UsageRevisionBase):
    def __init__(self, axiom, usage_id, read=True):
        super().__init__(axiom, usage_id, read=False)
        self._init_registers()
        if read:
            self.read()

    def _init_registers(self):
        self.reg_ae_status_running = 0
        self.reg_ae_status_clipping = 0
        self.reg_reduced_power_mode = 0
        self.reg_u83_cts_status = 0
        self.reg_u83_cds_status = 0
        self.reg_large_contact_suppressed = 0
        self.reg_palm_suppressed = 0
        self.reg_large_hover_suppressed = 0
        self.reg_phantom_force_detected = 0
        self.reg_excess_contact_suppressed = 0
        self.reg_cts_drifting_active = 0
        self.reg_cds_drifting_active = 0
        self.reg_u06_self_test_status = 0
        self.reg_u06_self_test_cause = 0
        self.reg_u06_self_test_number = 0
        self.reg_u06_self_test_overall_result = 0
        self.reg_u06_self_test_general_debug = 0
        self.reg_ae_self_test_frame_cts_clipping = 0
        self.reg_ae_self_test_frame_cts_overflow = 0
        self.reg_ae_self_test_frame_cds_clipping = 0
        self.reg_ae_self_test_frame_cds_overflow = 0
        self.reg_ae_self_test_frame_thermistor_clipping = 0
        self.reg_ae_self_test_frame_thermistor_overflow = 0
        self.reg_u06_self_test_results = [0] * 16
        self.reg_u83_self_test_frame_stats_cts_max = 0
        self.reg_u83_self_test_frame_stats_cts_min = 0
        self.reg_u83_self_test_frame_stats_cts_sum = 0
        self.reg_u83_self_test_frame_stats_cts_count = 0
        self.reg_u83_self_test_frame_stats_cts_peak2peak = 0
        self.reg_u83_self_test_frame_stats_cds_max = [0] * 26
        self.reg_u83_self_test_frame_stats_cds_min = [0] * 26
        self.reg_u83_self_test_frame_stats_cds_sum = [0] * 26
        self.reg_u83_self_test_frame_stats_cds_count = [0] * 26
        self.reg_u83_self_test_frame_stats_cds_peak2peak = [0] * 26
        self.reg_thermistor_reading = 0
        self.reg_gpio_status = 0
        self.reg_current_frame_rate = 0
        self.reg_u62_num_qualified_peaks = 0
        self.reg_u72_num_basic_peaks = 0
        self.reg_u83_channel_status_cts_state = [0] * 3
        self.reg_u83_channel_status_cds_state = [0] * 3
        self.reg_u83_channel_status_operating_point = [0] * 3
        self.reg_u83_channel_status_cts_noise = [0] * 3
        self.reg_u83_channel_status_cds_noise = [0] * 3
        self.reg_u83_channel_status_error_code = [0] * 3
        self.reg_u83_channel_status_cts_operating_point = [0] * 3
        self.reg_u83_channel_status_cds_operating_point = [0] * 3

    def unpack(self):
        field0, field1, field2, field3, field4, field5, field6 = struct.unpack("<H4B2H", bytes(bytearray(self._usage_binary_data[0:10])))
        self.reg_ae_status_running = (field0 & 0x0001)
        self.reg_ae_status_clipping = (field0 & 0x0002) >> 1
        self.reg_reduced_power_mode = (field0 & 0x0004) >> 2
        self.reg_u83_cts_status = (field0 & 0x0010) >> 4
        self.reg_u83_cds_status = (field0 & 0x0020) >> 5
        self.reg_large_contact_suppressed = (field0 & 0x0040) >> 6
        self.reg_palm_suppressed = (field0 & 0x0080) >> 7
        self.reg_large_hover_suppressed = (field0 & 0x0100) >> 8
        self.reg_phantom_force_detected = (field0 & 0x0200) >> 9
        self.reg_excess_contact_suppressed = (field0 & 0x0400) >> 10
        self.reg_cts_drifting_active = (field0 & 0x1000) >> 12
        self.reg_cds_drifting_active = (field0 & 0x2000) >> 13
        self.reg_u06_self_test_status = field1
        self.reg_u06_self_test_cause = field2
        self.reg_u06_self_test_number = field3
        self.reg_u06_self_test_overall_result = field4
        self.reg_u06_self_test_general_debug = field5
        self.reg_ae_self_test_frame_cts_clipping = (field6 & 0x0004) >> 2
        self.reg_ae_self_test_frame_cts_overflow = (field6 & 0x0010) >> 4
        self.reg_ae_self_test_frame_cds_clipping = (field6 & 0x0020) >> 5
        self.reg_ae_self_test_frame_cds_overflow = (field6 & 0x0040) >> 6
        self.reg_ae_self_test_frame_thermistor_clipping = (field6 & 0x0080) >> 7
        self.reg_ae_self_test_frame_thermistor_overflow = (field6 & 0x0100) >> 8

        field = struct.unpack("<16B", bytes(bytearray(self._usage_binary_data[10:26])))
        self.reg_u06_self_test_results = [*field, ]  # Convert tuple to list

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[26:38])))
        # Skip the trans middle stats

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[38:50])))
        # Skip the trans edge stats

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[50:62])))
        # Skip the trans corner stats

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[62:74])))
        # Skip abs rows stats

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[74:86])))
        self.reg_u83_self_test_frame_stats_cts_max = max
        self.reg_u83_self_test_frame_stats_cts_min = min
        self.reg_u83_self_test_frame_stats_cts_sum = sum
        self.reg_u83_self_test_frame_stats_cts_count = count
        self.reg_u83_self_test_frame_stats_cts_peak2peak = peak2peak

        # Unpack 26 sets of CDS stats
        for i in range(26):
            offset = 86 + i * 12
            max, min, sum, count, peak2peak = struct.unpack(
                "<2HI2H", bytes(bytearray(self._usage_binary_data[offset:offset+12]))
            )
            self.reg_u83_self_test_frame_stats_cds_max[i] = max
            self.reg_u83_self_test_frame_stats_cds_min[i] = min
            self.reg_u83_self_test_frame_stats_cds_sum[i] = sum
            self.reg_u83_self_test_frame_stats_cds_count[i] = count
            self.reg_u83_self_test_frame_stats_cds_peak2peak[i] = peak2peak

        # Update offsets for subsequent fields
        next_offset = 86 + 26 * 12  # 398
        
        field0, field1, field2, field3, field4 = struct.unpack("<3H2B", bytes(bytearray(self._usage_binary_data[next_offset:next_offset+8])))
        self.reg_thermistor_reading = field0
        self.reg_gpio_status = field1
        self.reg_current_frame_rate = field2
        self.reg_u62_num_qualified_peaks = field3
        self.reg_u72_num_basic_peaks = field4

        next_offset += 8
        field0, _, field1, field2 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[next_offset:next_offset+8])))
        self.reg_u83_channel_status_cts_state[0] = (field0 & 0x0038) >> 3
        self.reg_u83_channel_status_cds_state[0] = (field0 & 0x01C0) >> 6
        self.reg_u83_channel_status_operating_point[0] = (field0 & 0x1E00) >> 9
        self.reg_u83_channel_status_cts_noise[0] = field1
        self.reg_u83_channel_status_cds_noise[0] = field2

        next_offset += 8
        field0, _, field1, _, field2 = struct.unpack("<5H", bytes(bytearray(self._usage_binary_data[next_offset:next_offset+10])))
        self.reg_u83_channel_status_error_code[0] = field0 & 0x00FF
        self.reg_u83_channel_status_cts_operating_point[0] = field1
        self.reg_u83_channel_status_cds_operating_point[0] = field2

        next_offset += 10
        field0, _, field1, field2 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[next_offset:next_offset+8])))
        self.reg_u83_channel_status_cts_state[1] = (field0 & 0x0038) >> 3
        self.reg_u83_channel_status_cds_state[1] = (field0 & 0x01C0) >> 6
        self.reg_u83_channel_status_operating_point[1] = (field0 & 0x1E00) >> 9
        self.reg_u83_channel_status_cts_noise[1] = field1
        self.reg_u83_channel_status_cds_noise[1] = field2

        next_offset += 8
        field0, _, field1, _, field2 = struct.unpack("<5H", bytes(bytearray(self._usage_binary_data[next_offset:next_offset+10])))
        self.reg_u83_channel_status_error_code[1] = field0 & 0x00FF
        self.reg_u83_channel_status_cts_operating_point[1] = field1
        self.reg_u83_channel_status_cds_operating_point[1] = field2

        next_offset += 10
        field0, _, field1, field2 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[next_offset:next_offset+8])))
        self.reg_u83_channel_status_cts_state[2] = (field0 & 0x0038) >> 3
        self.reg_u83_channel_status_cds_state[2] = (field0 & 0x01C0) >> 6
        self.reg_u83_channel_status_operating_point[2] = (field0 & 0x1E00) >> 9
        self.reg_u83_channel_status_cts_noise[2] = field1
        self.reg_u83_channel_status_cds_noise[2] = field2

        next_offset += 8
        field0, _, field1, _, field2 = struct.unpack("<5H", bytes(bytearray(self._usage_binary_data[next_offset:next_offset+10])))
        self.reg_u83_channel_status_error_code[2] = field0 & 0x00FF
        self.reg_u83_channel_status_cts_operating_point[2] = field1
        self.reg_u83_channel_status_cds_operating_point[2] = field2

    def print_registers(self):
        print("u07 Live Data")
        print("  AE Running                 : %s" % ("Running" if self.reg_ae_status_running == 1 else "Not Running"))
        print("  AE Clipping                : %s" % ("Clipping" if self.reg_ae_status_clipping == 1 else "Not Clipping"))
        print("  Reduced Power Mode         : %s" % ("Full" if self.reg_reduced_power_mode == 0 else "Reduced"))
        print("  CTS Status                 : %s" % ("Ready" if self.reg_u83_cts_status == 1 else "Not Ready"))
        print("  CDS Status                 : %s" % ("Ready" if self.reg_u83_cds_status == 1 else "Not Ready"))
        print("  Large Contact Suppressed   : %s" % ("Yes" if self.reg_large_contact_suppressed == 1 else "No"))
        print("  Palm Suppressed            : %s" % ("Yes" if self.reg_palm_suppressed == 1 else "No"))
        print("  Large Hover Suppressed     : %s" % ("Yes" if self.reg_large_hover_suppressed == 1 else "No"))
        print("  Phantom Force Detected     : %s" % ("Yes" if self.reg_phantom_force_detected == 1 else "No"))
        print("  Excess Contacts Suppressed : %s" % ("Yes" if self.reg_excess_contact_suppressed == 1 else "No"))
        print("")
        print("  Drifting Indicators")
        print("    CTS Drifting   : %s" % ("Drifting" if self.reg_cts_drifting_active == 1 else "Not Drifting"))
        print("    CDS Drifting   : %s" % ("Drifting" if self.reg_cds_drifting_active == 1 else "Not Drifting"))
        print("")
        print("  Self Test Status")
        print("    u06 Self Test Status               : %s" % ("Idle" if self.reg_u06_self_test_status == 0 else "Busy"))
        print("    u06 Self Test Triggered By         : %s" % u07_Utils.convert_self_test_cause_to_string(self.reg_u06_self_test_cause))
        print("    u06 Self Test Current Test Running : %u" % self.reg_u06_self_test_number)
        print("    u06 Self Test Overall Result       : %s" % u07_Utils.convert_self_test_overall_result_to_string(self.reg_u06_self_test_overall_result))
        print("    u06 Self Test Debug Data           : %u" % self.reg_u06_self_test_general_debug)
        print("")
        print("  Self Test Results")
        print("    Test  0 CPU RAM Test                      : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[0]))
        print("    Test  1 AE Baseline RAM Test              : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[1]))
        print("    Test  2 AE Internal RAM Test              : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[2]))
        print("    Test  3 VDDA Test                         : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[3]))
        print("    Test  4 AE Test                           : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[4]))
        print("    Test  5 Sense and Shield Pin Leakage Test : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[5]))
        print("    Test  7 CTS Cap Signal Limits Test        : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[7]))
        print("    Test  8 CDS Signal Limits Test            : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[8]))
        print("    Test  9 CRC Generate and Check Test       : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[9]))
        print("    Test 10 nIRQ Pin Test                     : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[10]))
        print("    Test 11 NVM Test                          : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[11]))
        print("    Test 12 RTC Test                          : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[12]))
        print("    Test 13 VDDC Test                         : %s" % u07_Utils.convert_self_test_result_to_string(self.reg_u06_self_test_results[13]))
        print("")
        print("  GPIOs State")
        print("    GPIO  : 0 1 2")
        print("    State : %u %u %u" % ((self.reg_gpio_status & 0x1), (self.reg_gpio_status & 0x2) >> 1, (self.reg_gpio_status & 0x4) >> 2))
        print("")
        print("  AE Frame Rate")
        print("    Current Frame Rate : %u Hz" % self.reg_current_frame_rate)
        print("")
        print("  Self Test 7 - CTS Cap Signal Limits")
        print("    Node Max                   : %5u" % self.reg_u83_self_test_frame_stats_cts_max)
        print("    Node Min                   : %5u" % self.reg_u83_self_test_frame_stats_cts_min)
        print("    Sum of Nodes               : %5u" % self.reg_u83_self_test_frame_stats_cts_sum)
        print("    Number of Nodes            : %5u" % self.reg_u83_self_test_frame_stats_cts_count)
        print("")
        print("  Self Test 8 - CDS Signal Limits")
        for i in range(0, 26, 13):
            channel_range = range(i, min(i+13, 26))
            header = "    Channel :" + ''.join([f" {ch:5}" for ch in channel_range])
            values = "    Signal  :" + ''.join([f" {self.reg_u83_self_test_frame_stats_cds_max[ch]:5}" for ch in channel_range])
            print(header)
            print(values)
        print("")
        print("  u83 Channel Status")
        print("    Channel     : %13s %13s %13s" % ("0".center(13), "1".center(13), "2".center(13)))
        print("    CTS State   : %13s %13s %13s" % (u07_Utils.convert_u83_channel_state_to_string(self.reg_u83_channel_status_cts_state[0]), u07_Utils.convert_u83_channel_state_to_string(self.reg_u83_channel_status_cts_state[1]), u07_Utils.convert_u83_channel_state_to_string(self.reg_u83_channel_status_cts_state[2])))
        print("    CDS State   : %13s %13s %13s" % (u07_Utils.convert_u83_channel_state_to_string(self.reg_u83_channel_status_cds_state[0]), u07_Utils.convert_u83_channel_state_to_string(self.reg_u83_channel_status_cds_state[1]), u07_Utils.convert_u83_channel_state_to_string(self.reg_u83_channel_status_cds_state[2])))
        print("    Active OP   : %13u %13u %13u" % (self.reg_u83_channel_status_operating_point[0], self.reg_u83_channel_status_operating_point[1], self.reg_u83_channel_status_operating_point[2]))
        print("    CTS Noise   : %12s%% %12s%% %12s%%" % (u07_Utils.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_cts_noise[0]), u07_Utils.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_cts_noise[1]), u07_Utils.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_cts_noise[2])))
        print("    CDS Noise   : %12s%% %12s%% %12s%%" % (u07_Utils.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_cds_noise[0]), u07_Utils.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_cds_noise[1]), u07_Utils.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_cds_noise[2])))
        print("")
        print("  u83 Channel Status")
        print("     Channel                         : %13s %13s %13s" % ("0".center(13), "1".center(13), "2".center(13)))
        print("     AutoTune Error                  : %13s %13s %13s" % (u07_Utils.convert_self_test_result_to_string(self.reg_u83_channel_status_error_code[0]), u07_Utils.convert_self_test_result_to_string(self.reg_u83_channel_status_error_code[1]), u07_Utils.convert_self_test_result_to_string(self.reg_u83_channel_status_error_code[2])))
        print("     CTS Cols Operating Point Errors : %13s %13s %13s" % (u07_Utils.convert_self_test_result_to_string(self.reg_u83_channel_status_cts_operating_point[0]), u07_Utils.convert_self_test_result_to_string(self.reg_u83_channel_status_cts_operating_point[1]), u07_Utils.convert_self_test_result_to_string(self.reg_u83_channel_status_cts_operating_point[2])))
        print("     CDS Operating Point Errors      : %13s %13s %13s" % (u07_Utils.convert_self_test_result_to_string(self.reg_u83_channel_status_cds_operating_point[0]), u07_Utils.convert_self_test_result_to_string(self.reg_u83_channel_status_cds_operating_point[1]), u07_Utils.convert_self_test_result_to_string(self.reg_u83_channel_status_cds_operating_point[2])))
        print("")
        print("  Self Test AE Frame Status")
        print("    CTS Cols Clipping     : %s" % ("Clipping" if self.reg_ae_self_test_frame_cts_clipping == 1 else "Not Clipping"))
        print("    CTS Overflow          : %s" % ("Overflow" if self.reg_ae_self_test_frame_cts_overflow == 1 else "Not Overflow"))
        print("    CDS Clipping          : %s" % ("Clipping" if self.reg_ae_self_test_frame_cds_clipping == 1 else "Not Clipping"))
        print("    CDS Overflow          : %s" % ("Overflow" if self.reg_ae_self_test_frame_cds_overflow == 1 else "Not Overflow"))
        print("    Thermistor Clipping   : %s" % ("Clipping" if self.reg_ae_self_test_frame_thermistor_clipping == 1 else "Not Clipping"))
        print("    Thermistor Overflow   : %s" % ("Overflow" if self.reg_ae_self_test_frame_thermistor_overflow == 1 else "Not Overflow"))
        print("    Thermistor Reading    : %u" % self.reg_thermistor_reading)
