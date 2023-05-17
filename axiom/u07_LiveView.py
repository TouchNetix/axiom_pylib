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

class u07_LiveView:
    USAGE_ID = 0x07

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

    def write(self):
        self.read() # u07 is read-only. If any changes have been made, overwrite them with the contents from the device
        raise Exception("Cannot write to u07. u07 is a read-only usage.")
    
    def print(self):
        self._print_registers()

    def _unpack(self):
        self._unpack_registers()

#region Value to String Conversions
    def convert_self_test_cause_to_string(self, cause):
        if cause == 0:
            return "Boot"
        elif cause == 1:
            return "Heartbeat"
        elif cause == 2:
            return "Host Triggered"
        else:
            return "<UNKNOWN_CAUSE>"
            
    def convert_self_test_overall_result_to_string(self, overall_result):
        if overall_result == 0x01:
            return "In Progress"
        elif overall_result == 0x02:
            return "Pass"
        elif overall_result == 0x7D:
            return "No Tests Done"
        elif overall_result == 0x7F:
            return "Never Run"
        elif overall_result == 0x80:
            return "Fail"
        else:
            return "<UNKNOWN_OVERALL_RESULT>"
        
    def convert_self_test_result_to_string(self, result):
        if result == 0x00:
            return "Not Yet Run"
        elif result == 0x01:
            return "In Progress"
        elif result == 0x02:
            return "Pass"
        elif result == 0x03:
            return "Must Retry"
        elif result == 0x7E:
            return "Not Implemented"
        elif result == 0x7F:
            return "Never Run"
        elif (result & 0x80) != 0:
            return "Fail (Extended Error Bits: 0x%02X)" % (result & 0x7F)
        else:
            return "<UNKNOWN_SELF_TEST_RESULT>"
        
    def convert_u83_channel_state_to_string(self, state):
        if state == 0:
            return "Scan"
        elif state == 1:
            return "Capture"
        elif state == 2:
            return "Settle"
        elif state == 3:
            return "Qualification"
        elif state == 4:
            return "Ready"
        elif state == 5:
            return "Noisy"
        elif state == 6:
            return "Inactive"
        elif state == 7:
            return "Reset"
        else:
            return "<UNKNOWN_U83_CHANNEL_STATE>"
            
    def convert_u83_measurement_noise_to_string(self, noise_as_float100):
        return "%.2f" % (float(noise_as_float100) / 100)
#endregion

#region u07 Live View Usage Revision 6
    def _init_registers_uifrev6(self):
        self.reg_ae_status_running                                 = 0
        self.reg_ae_status_clipping                                = 0
        self.reg_reduced_power_mode                                = 0
        self.reg_u83_trans_status                                  = 0
        self.reg_u83_abs_status                                    = 0
        self.reg_u83_aux_status                                    = 0
        self.reg_large_contact_suppressed                          = 0
        self.reg_palm_suppressed                                   = 0
        self.reg_large_hover_suppressed                            = 0
        self.reg_phantom_force_detected                            = 0
        self.reg_excess_contact_suppressed                         = 0
        self.reg_trans_drifting_active                             = 0
        self.reg_abs_drifting_active                               = 0
        self.reg_aux_drifting_active                               = 0
        self.reg_u06_self_test_status                              = 0
        self.reg_u06_self_test_cause                               = 0
        self.reg_u06_self_test_number                              = 0
        self.reg_u06_self_test_overall_result                      = 0
        self.reg_u06_self_test_general_debug                       = 0
        self.reg_u06_self_test_results                             = [0] * 16
        self.reg_u83_self_test_frame_stats_trans_middle_max        = 0
        self.reg_u83_self_test_frame_stats_trans_middle_min        = 0
        self.reg_u83_self_test_frame_stats_trans_middle_sum        = 0
        self.reg_u83_self_test_frame_stats_trans_middle_count      = 0
        self.reg_u83_self_test_frame_stats_trans_middle_peak2peak  = 0
        self.reg_u83_self_test_frame_stats_trans_edges_max         = 0
        self.reg_u83_self_test_frame_stats_trans_edges_min         = 0
        self.reg_u83_self_test_frame_stats_trans_edges_sum         = 0
        self.reg_u83_self_test_frame_stats_trans_edges_count       = 0
        self.reg_u83_self_test_frame_stats_trans_edges_peak2peak   = 0
        self.reg_u83_self_test_frame_stats_trans_corners_max       = 0
        self.reg_u83_self_test_frame_stats_trans_corners_min       = 0
        self.reg_u83_self_test_frame_stats_trans_corners_sum       = 0
        self.reg_u83_self_test_frame_stats_trans_corners_count     = 0
        self.reg_u83_self_test_frame_stats_trans_corners_peak2peak = 0
        self.reg_u83_self_test_frame_stats_abs_rows_max            = 0
        self.reg_u83_self_test_frame_stats_abs_rows_min            = 0
        self.reg_u83_self_test_frame_stats_abs_rows_sum            = 0
        self.reg_u83_self_test_frame_stats_abs_rows_count          = 0
        self.reg_u83_self_test_frame_stats_abs_rows_peak2peak      = 0
        self.reg_u83_self_test_frame_stats_abs_cols_max            = 0
        self.reg_u83_self_test_frame_stats_abs_cols_min            = 0
        self.reg_u83_self_test_frame_stats_abs_cols_sum            = 0
        self.reg_u83_self_test_frame_stats_abs_cols_count          = 0
        self.reg_u83_self_test_frame_stats_abs_cols_peak2peak      = 0
        self.reg_u83_self_test_frame_stats_aux_max                 = [0] * 4
        self.reg_u83_self_test_frame_stats_aux_min                 = [0] * 4
        self.reg_u83_self_test_frame_stats_aux_sum                 = [0] * 4
        self.reg_u83_self_test_frame_stats_aux_count               = [0] * 4
        self.reg_u83_self_test_frame_stats_aux_peak2peak           = [0] * 4
        self.reg_gpio_status                                       = 0
        self.reg_current_frame_rate                                = 0
        self.reg_u62_num_qualified_peaks                           = 0
        self.reg_u72_num_basic_peaks                               = 0
        self.reg_u83_channel_status_trans_state                    = [0] * 3
        self.reg_u83_channel_status_abs_state                      = [0] * 3
        self.reg_u83_channel_status_aux_state                      = [0] * 3
        self.reg_u83_channel_status_operating_point                = [0] * 3
        self.reg_u83_channel_status_trans_noise                    = [0] * 3
        self.reg_u83_channel_status_abs_noise                      = [0] * 3
        self.reg_u83_channel_status_aux_noise                      = [0] * 3

    def _unpack_uifrev6(self):
        field0, field1, field2, field3, field4, field5 = struct.unpack("<H4BH", bytes(bytearray(self._usage_binary_data[0:8])))
        self.reg_ae_status_running            = (field0 & 0x0001)
        self.reg_ae_status_clipping           = (field0 & 0x0002) >>  1
        self.reg_reduced_power_mode           = (field0 & 0x0004) >>  2
        self.reg_u83_trans_status             = (field0 & 0x0008) >>  3
        self.reg_u83_abs_status               = (field0 & 0x0010) >>  4
        self.reg_u83_aux_status               = (field0 & 0x0020) >>  5
        self.reg_large_contact_suppressed     = (field0 & 0x0040) >>  6
        self.reg_palm_suppressed              = (field0 & 0x0080) >>  7
        self.reg_large_hover_suppressed       = (field0 & 0x0100) >>  8
        self.reg_phantom_force_detected       = (field0 & 0x0200) >>  9
        self.reg_excess_contact_suppressed    = (field0 & 0x0400) >> 10
        self.reg_trans_drifting_active        = (field0 & 0x0800) >> 11
        self.reg_abs_drifting_active          = (field0 & 0x1000) >> 12
        self.reg_aux_drifting_active          = (field0 & 0x2000) >> 13
        self.reg_u06_self_test_status         =  field1
        self.reg_u06_self_test_cause          =  field2
        self.reg_u06_self_test_number         =  field3
        self.reg_u06_self_test_overall_result =  field4
        self.reg_u06_self_test_general_debug  =  field5

        field = struct.unpack("<16B", bytes(bytearray(self._usage_binary_data[8:24])))
        self.reg_u06_self_test_results = [*field,] # Convert tuple to list

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[24:36])))
        self.reg_u83_self_test_frame_stats_trans_middle_max        = max
        self.reg_u83_self_test_frame_stats_trans_middle_min        = min
        self.reg_u83_self_test_frame_stats_trans_middle_sum        = sum
        self.reg_u83_self_test_frame_stats_trans_middle_count      = count
        self.reg_u83_self_test_frame_stats_trans_middle_peak2peak  = peak2peak

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[36:48])))
        self.reg_u83_self_test_frame_stats_trans_edges_max         = max
        self.reg_u83_self_test_frame_stats_trans_edges_min         = min
        self.reg_u83_self_test_frame_stats_trans_edges_sum         = sum
        self.reg_u83_self_test_frame_stats_trans_edges_count       = count
        self.reg_u83_self_test_frame_stats_trans_edges_peak2peak   = peak2peak

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[48:60])))
        self.reg_u83_self_test_frame_stats_trans_corners_max       = max
        self.reg_u83_self_test_frame_stats_trans_corners_min       = min
        self.reg_u83_self_test_frame_stats_trans_corners_sum       = sum
        self.reg_u83_self_test_frame_stats_trans_corners_count     = count
        self.reg_u83_self_test_frame_stats_trans_corners_peak2peak = peak2peak

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[60:72])))
        self.reg_u83_self_test_frame_stats_abs_rows_max       = max
        self.reg_u83_self_test_frame_stats_abs_rows_min       = min
        self.reg_u83_self_test_frame_stats_abs_rows_sum       = sum
        self.reg_u83_self_test_frame_stats_abs_rows_count     = count
        self.reg_u83_self_test_frame_stats_abs_rows_peak2peak = peak2peak

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[72:84])))
        self.reg_u83_self_test_frame_stats_abs_cols_max       = max
        self.reg_u83_self_test_frame_stats_abs_cols_min       = min
        self.reg_u83_self_test_frame_stats_abs_cols_sum       = sum
        self.reg_u83_self_test_frame_stats_abs_cols_count     = count
        self.reg_u83_self_test_frame_stats_abs_cols_peak2peak = peak2peak

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[84:96])))
        self.reg_u83_self_test_frame_stats_aux_max[0]       = max
        self.reg_u83_self_test_frame_stats_aux_min[0]       = min
        self.reg_u83_self_test_frame_stats_aux_sum[0]       = sum
        self.reg_u83_self_test_frame_stats_aux_count[0]     = count
        self.reg_u83_self_test_frame_stats_aux_peak2peak[0] = peak2peak
        
        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[96:108])))
        self.reg_u83_self_test_frame_stats_aux_max[1]       = max
        self.reg_u83_self_test_frame_stats_aux_min[1]       = min
        self.reg_u83_self_test_frame_stats_aux_sum[1]       = sum
        self.reg_u83_self_test_frame_stats_aux_count[1]     = count
        self.reg_u83_self_test_frame_stats_aux_peak2peak[1] = peak2peak

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[108:120])))
        self.reg_u83_self_test_frame_stats_aux_max[2]       = max
        self.reg_u83_self_test_frame_stats_aux_min[2]       = min
        self.reg_u83_self_test_frame_stats_aux_sum[2]       = sum
        self.reg_u83_self_test_frame_stats_aux_count[2]     = count
        self.reg_u83_self_test_frame_stats_aux_peak2peak[2] = peak2peak

        max, min, sum, count, peak2peak = struct.unpack("<2HI2H", bytes(bytearray(self._usage_binary_data[120:132])))
        self.reg_u83_self_test_frame_stats_aux_max[3]       = max
        self.reg_u83_self_test_frame_stats_aux_min[3]       = min
        self.reg_u83_self_test_frame_stats_aux_sum[3]       = sum
        self.reg_u83_self_test_frame_stats_aux_count[3]     = count
        self.reg_u83_self_test_frame_stats_aux_peak2peak[3] = peak2peak

        field0, field1, field2, field3 = struct.unpack("<2H2B", bytes(bytearray(self._usage_binary_data[132:138])))
        self.reg_gpio_status             = field0
        self.reg_current_frame_rate      = field1
        self.reg_u62_num_qualified_peaks = field2
        self.reg_u72_num_basic_peaks     = field3

        field0, field1, field2, field3 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[138:146])))
        self.reg_u83_channel_status_trans_state[0]     = (field0 & 0x0007)
        self.reg_u83_channel_status_abs_state[0]       = (field0 & 0x0038) >> 3
        
        self.reg_u83_channel_status_aux_state[0]       = (field0 & 0x01C0) >> 6
        self.reg_u83_channel_status_operating_point[0] = (field0 & 0x1E00) >> 9
        self.reg_u83_channel_status_trans_noise[0]     =  field1
        self.reg_u83_channel_status_abs_noise[0]       =  field2
        self.reg_u83_channel_status_aux_noise[0]       =  field3

        field0, field1, field2, field3 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[146:154])))
        self.reg_u83_channel_status_trans_state[1]     = (field0 & 0x0007)
        self.reg_u83_channel_status_abs_state[1]       = (field0 & 0x0038) >> 3
        self.reg_u83_channel_status_aux_state[1]       = (field0 & 0x01C0) >> 6
        self.reg_u83_channel_status_operating_point[1] = (field0 & 0x1E00) >> 9
        self.reg_u83_channel_status_trans_noise[1]     =  field1
        self.reg_u83_channel_status_abs_noise[1]       =  field2
        self.reg_u83_channel_status_aux_noise[1]       =  field3

        field0, field1, field2, field3 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[154:162])))
        self.reg_u83_channel_status_trans_state[2]     = (field0 & 0x0007)
        self.reg_u83_channel_status_abs_state[2]       = (field0 & 0x0038) >> 3
        self.reg_u83_channel_status_aux_state[2]       = (field0 & 0x01C0) >> 6
        self.reg_u83_channel_status_operating_point[2] = (field0 & 0x1E00) >> 9
        self.reg_u83_channel_status_trans_noise[2]     =  field1
        self.reg_u83_channel_status_abs_noise[2]       =  field2
        self.reg_u83_channel_status_aux_noise[2]       =  field3

    def _print_registers_uifrev6(self):
        print("u07 Live Data")
        print("  AE Running                 : %s" % ("Running" if self.reg_ae_status_running == 1 else "Not Running"))
        print("  AE Clipping                : %s" % ("Clipping" if self.reg_ae_status_clipping == 1 else "Not Clipping"))
        print("  Reduced Power Mode         : %s" % ("Full" if self.reg_reduced_power_mode == 0 else "Reduced"))
        print("  Trans Status               : %s" % ("Ready" if self.reg_u83_trans_status == 1 else "Not Ready"))
        print("  Abs Status                 : %s" % ("Ready" if self.reg_u83_abs_status == 1 else "Not Ready"))
        print("  Aux Status                 : %s" % ("Ready" if self.reg_u83_aux_status == 1 else "Not Ready"))
        print("  Large Contact Suppressed   : %s" % ("Yes" if self.reg_large_contact_suppressed == 1 else "No"))
        print("  Palm Suppressed            : %s" % ("Yes" if self.reg_palm_suppressed == 1 else "No"))
        print("  Large Hover Suppressed     : %s" % ("Yes" if self.reg_large_hover_suppressed == 1 else "No"))
        print("  Phantom Force Detected     : %s" % ("Yes" if self.reg_phantom_force_detected == 1 else "No"))
        print("  Excess Contacts Suppressed : %s" % ("Yes" if self.reg_excess_contact_suppressed == 1 else "No"))
        print("")
        print("  Drifting Indicators")
        print("  Trans Drifting : %s" % ("Drifting" if self.reg_trans_drifting_active == 1 else "Not Drifting"))
        print("  Abs Drifiting  : %s" % ("Drifting" if self.reg_abs_drifting_active == 1 else "Not Drifting"))
        print("  Aux Drifting   : %s" % ("Drifting" if self.reg_aux_drifting_active == 1 else "Not Drifting"))
        print("")
        print("  Self Test Status")
        print("    u06 Self Test Status               : %s" % ("Idle" if self.reg_u06_self_test_status == 0 else "Busy"))
        print("    u06 Self Test Triggered By         : %s" % self.convert_self_test_cause_to_string(self.reg_u06_self_test_cause))
        print("    u06 Self Test Current Test Running : %u" % self.reg_u06_self_test_number)
        print("    u06 Self Test Overall Result       : %s" % self.convert_self_test_overall_result_to_string(self.reg_u06_self_test_overall_result))
        print("    u06 Self Test Debug Data           : %u" % self.reg_u06_self_test_general_debug)
        print("")
        print("  Self Test Results")
        print("    Test  0 CPU RAM Test                      : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 0]))
        print("    Test  1 AE Baseline RAM Test              : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 1]))
        print("    Test  2 AE Internal RAM Test              : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 2]))
        print("    Test  3 VDDA Test                         : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 3]))
        print("    Test  4 AE Test                           : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 4]))
        print("    Test  5 Sense and Shield Pin Leakage Test : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 5]))
        print("    Test  6 Trans Cap Signal Limits Test      : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 6]))
        print("    Test  7 Abs Cap Signal Limits Test        : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 7]))
        print("    Test  8 AUX Signal Limits Test            : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 8]))
        print("    Test  9 CRC Generate and Check Test       : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[ 9]))
        print("    Test 10 nIRQ Pin Test                     : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[10]))
        print("    Test 11 NVM Test                          : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[11]))
        print("    Test 12 RTC Test                          : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[12]))
        print("    Test 13 VDDC Test                         : %s" % self.convert_self_test_result_to_string(self.reg_u06_self_test_results[13]))
        print("")
        print("GPIOs State")
        print("  GPIO  : 0 1 2")
        print("  State : %u %u %u" % ((self.reg_gpio_status & 0x1), (self.reg_gpio_status & 0x2) >> 1, (self.reg_gpio_status & 0x4) >> 2))
        print("AE Frame Rate")
        print("  Current Frame Rate: %u Hz" % self.reg_current_frame_rate)
        print("")
        print("  Self Test 6 - Trans Cap Signal Limits")
        print("    Middle Nodes")
        print("      Node Max                   : %5u" % self.reg_u83_self_test_frame_stats_trans_middle_max)
        print("      Node Min                   : %5u" % self.reg_u83_self_test_frame_stats_trans_middle_min)
        print("      Sum of Nodes               : %5u" % self.reg_u83_self_test_frame_stats_trans_middle_sum)
        print("      Number of Nodes            : %5u" % self.reg_u83_self_test_frame_stats_trans_middle_count)
        print("      Node Peak-2-peak Variation : %5u" % self.reg_u83_self_test_frame_stats_trans_middle_peak2peak)
        print("    Edge Nodes")
        print("      Node Max                   : %5u" % self.reg_u83_self_test_frame_stats_trans_edges_max)
        print("      Node Min                   : %5u" % self.reg_u83_self_test_frame_stats_trans_edges_min)
        print("      Sum of Nodes               : %5u" % self.reg_u83_self_test_frame_stats_trans_edges_sum)
        print("      Number of Nodes            : %5u" % self.reg_u83_self_test_frame_stats_trans_edges_count)
        print("    Corner Nodes")
        print("      Node Max                   : %5u" % self.reg_u83_self_test_frame_stats_trans_corners_min)
        print("      Node Min                   : %5u" % self.reg_u83_self_test_frame_stats_trans_corners_min)
        print("")
        print("  Self Test 7 - Abs Cap Signal Limits")
        print("    Rows")
        print("      Node Max                   : %5u" % self.reg_u83_self_test_frame_stats_abs_rows_max)
        print("      Node Min                   : %5u" % self.reg_u83_self_test_frame_stats_abs_rows_min)
        print("      Sum of Nodes               : %5u" % self.reg_u83_self_test_frame_stats_abs_rows_sum)
        print("      Number of Nodes            : %5u" % self.reg_u83_self_test_frame_stats_abs_rows_count)
        print("    Columns")
        print("      Node Max                   : %5u" % self.reg_u83_self_test_frame_stats_abs_cols_max)
        print("      Node Min                   : %5u" % self.reg_u83_self_test_frame_stats_abs_cols_min)
        print("      Sum of Nodes               : %5u" % self.reg_u83_self_test_frame_stats_abs_cols_sum)
        print("      Number of Nodes            : %5u" % self.reg_u83_self_test_frame_stats_abs_cols_count)
        print("")
        print("  Self Test 8 - Aux Signal Limits")
        print("            %5s %5s %5s %5s" % ("0".center(5), "1".center(5), "2".center(5), "3".center(5)))
        print("    Channel %5u %5u %5u %5u" % (self.reg_u83_self_test_frame_stats_aux_max[0], self.reg_u83_self_test_frame_stats_aux_max[1], self.reg_u83_self_test_frame_stats_aux_max[2], self.reg_u83_self_test_frame_stats_aux_max[3]))
        print("")
        print("  u83 Channel Status")
        print("                  %13s %13s %13s" % ("0".center(13), "1".center(13), "2".center(13)))
        print("    Trans State : %13s %13s %13s" % (self.convert_u83_channel_state_to_string(self.reg_u83_channel_status_trans_state[0]), self.convert_u83_channel_state_to_string(self.reg_u83_channel_status_trans_state[1]), self.convert_u83_channel_state_to_string(self.reg_u83_channel_status_trans_state[2])))
        print("    Abs State   : %13s %13s %13s" % (self.convert_u83_channel_state_to_string(self.reg_u83_channel_status_abs_state[0]),   self.convert_u83_channel_state_to_string(self.reg_u83_channel_status_abs_state[1]),   self.convert_u83_channel_state_to_string(self.reg_u83_channel_status_abs_state[2])))
        print("    Aux State   : %13s %13s %13s" % (self.convert_u83_channel_state_to_string(self.reg_u83_channel_status_aux_state[0]),   self.convert_u83_channel_state_to_string(self.reg_u83_channel_status_aux_state[1]), self.convert_u83_channel_state_to_string(self.reg_u83_channel_status_aux_state[2])))
        print("    Active OP   : %13u %13u %13u" % (self.reg_u83_channel_status_operating_point[0], self.reg_u83_channel_status_operating_point[1], self.reg_u83_channel_status_operating_point[2]))
        print("    Trans Noise : %12s%% %12s%% %12s%%" % (self.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_trans_noise[0]), self.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_trans_noise[1]), self.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_trans_noise[2])))
        print("    Abs Noise   : %12s%% %12s%% %12s%%" % (self.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_abs_noise[0]),   self.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_abs_noise[1]),   self.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_abs_noise[2])))
        print("    Aux Noise   : %12s%% %12s%% %12s%%" % (self.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_aux_noise[0]),   self.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_aux_noise[1]),   self.convert_u83_measurement_noise_to_string(self.reg_u83_channel_status_aux_noise[2])))
#endregion