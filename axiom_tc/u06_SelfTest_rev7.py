# Copyright (c) 2025 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from .UsageRevisionBase import UsageRevisionBase
import struct

class u06_SelfTestRev7(UsageRevisionBase):
    def __init__(self, axiom, usage_id, read=True):
        super().__init__(axiom, usage_id, read=False)
        self._init_registers()
        if read:
            self.read()

    def _init_registers(self):
        self.reg_enable_self_test_on_boot = 0
        self.reg_enable_self_test_on_heartbeat = 0
        self.reg_stop_tests_on_first_error = 0
        self.reg_enable_u83_self_test_frames = 0
        self.reg_fast_self_test_frames_after_reset = 0
        self.reg_u83_self_test_every_n_frames = 0
        self.reg_u83_self_test_jump = 0
        self.reg_aux_channels_use_calibration_capacitors = 0
        self.reg_aux_uses_thermistor = 0

        self.reg_run_test_on_boot_0_cpu_ram_test = 0
        self.reg_run_test_on_boot_1_ae_baseline_ram_test = 0
        self.reg_run_test_on_boot_2_ae_internal_test = 0
        self.reg_run_test_on_boot_3_vdda_test = 0
        self.reg_run_test_on_boot_4_ae_test = 0
        self.reg_run_test_on_boot_5_sense_and_sheild_pin_leakage_test = 0
        self.reg_run_test_on_boot_9_crc_check_test = 0
        self.reg_run_test_on_boot_11_nvm_test = 0
        self.reg_run_test_on_boot_12_rtc_test = 0
        self.reg_run_test_on_boot_13_vddc_ram_test = 0

        self.reg_run_test_on_heartbeat_8_aux_signal_limit_test = 0
        self.reg_run_test_on_heartbeat_9_crc_check_ram_test = 0
        self.reg_run_test_on_heartbeat_10_nirq_pin_test = 0
        self.reg_run_test_on_heartbeat_11_nvm_test = 0

        self.reg_run_test_on_host_trigger_1_ae_baseline_ram_test = 0
        self.reg_run_test_on_host_trigger_2_ae_internal_ram_test = 0
        self.reg_run_test_on_host_trigger_3_vdda_test = 0
        self.reg_run_test_on_host_trigger_4_ae_test = 0
        self.reg_run_test_on_host_trigger_5_sense_and_shield_pin_leakage_test = 0
        self.reg_run_test_on_host_trigger_8_aux_signal_limit_test = 0
        self.reg_run_test_on_host_trigger_9_crc_check_test = 0
        self.reg_run_test_on_host_trigger_10_nirq_pin_test = 0
        self.reg_run_test_on_host_trigger_11_nvm_test = 0
        self.reg_run_test_on_host_trigger_13_vddc_test = 0

        self.reg_self_test_5_sense_pins_pin_sense_mask = [0] * 16
        self.reg_self_test_5_sense_pins_gross_leakage_limit = 0
        self.reg_self_test_5_sense_pins_marginal_leakage_limit = 0
        self.reg_self_test_5_sense_pins_shield_gross_leakage_limit = 0
        self.reg_self_test_5_sense_pins_shield_marginal_leakage_limit = 0

        self.reg_self_test_8_aux_limits_chan_n_chan_max = [0] * 16
        self.reg_self_test_8_aux_limits_chan_n_chan_min = [0] * 16

    def unpack(self):
        field0, field1, field2, field3 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[0:8])))
        self.reg_enable_self_test_on_boot                = (field0 & 0x0001)
        self.reg_enable_self_test_on_heartbeat           = (field0 & 0x0002) >> 1
        self.reg_stop_tests_on_first_error               = (field1 & 0x0001)
        self.reg_enable_u83_self_test_frames             = (field1 & 0x0002) >> 1
        self.reg_fast_self_test_frames_after_reset       = (field1 & 0x0004) >> 2
        self.reg_u83_self_test_every_n_frames            = (field1 & 0xFFF0) >> 4
        self.reg_u83_self_test_jump                      = field2
        self.reg_aux_channels_use_calibration_capacitors = (field3 & 0x0001)
        self.reg_aux_uses_thermistor                     = (field3 & 0x0002) >> 1

        field0, field1, field2 = struct.unpack("<3H", bytes(bytearray(self._usage_binary_data[8:14])))
        self.reg_run_test_on_boot_0_cpu_ram_test                              = (field0 & 0x0001)
        self.reg_run_test_on_boot_1_ae_baseline_ram_test                      = (field0 & 0x0002) >> 1
        self.reg_run_test_on_boot_2_ae_internal_test                          = (field0 & 0x0004) >> 2
        self.reg_run_test_on_boot_3_vdda_test                                 = (field0 & 0x0008) >> 3
        self.reg_run_test_on_boot_4_ae_test                                   = (field0 & 0x0010) >> 4
        self.reg_run_test_on_boot_5_sense_and_sheild_pin_leakage_test         = (field0 & 0x0020) >> 5
        self.reg_run_test_on_boot_9_crc_check_test                            = (field0 & 0x0200) >> 9
        self.reg_run_test_on_boot_11_nvm_test                                 = (field0 & 0x0800) >> 11
        self.reg_run_test_on_boot_12_rtc_test                                 = (field0 & 0x1000) >> 12
        self.reg_run_test_on_boot_13_vddc_ram_test                            = (field0 & 0x2000) >> 13

        self.reg_run_test_on_heartbeat_8_aux_signal_limit_test                = (field1 & 0x0100) >> 8
        self.reg_run_test_on_heartbeat_9_crc_check_ram_test                   = (field1 & 0x0200) >> 9
        self.reg_run_test_on_heartbeat_10_nirq_pin_test                       = (field1 & 0x0400) >> 10
        self.reg_run_test_on_heartbeat_11_nvm_test                            = (field1 & 0x0800) >> 11

        self.reg_run_test_on_host_trigger_1_ae_baseline_ram_test              = (field2 & 0x0002) >> 1
        self.reg_run_test_on_host_trigger_2_ae_internal_ram_test              = (field2 & 0x0004) >> 2
        self.reg_run_test_on_host_trigger_3_vdda_test                         = (field2 & 0x0008) >> 3
        self.reg_run_test_on_host_trigger_4_ae_test                           = (field2 & 0x0010) >> 4
        self.reg_run_test_on_host_trigger_5_sense_and_shield_pin_leakage_test = (field2 & 0x0020) >> 5
        self.reg_run_test_on_host_trigger_8_aux_signal_limit_test             = (field2 & 0x0100) >> 8
        self.reg_run_test_on_host_trigger_9_crc_check_test                    = (field2 & 0x0200) >> 9
        self.reg_run_test_on_host_trigger_10_nirq_pin_test                    = (field2 & 0x0400) >> 10
        self.reg_run_test_on_host_trigger_11_nvm_test                         = (field2 & 0x0800) >> 11
        self.reg_run_test_on_host_trigger_13_vddc_test                        = (field2 & 0x2000) >> 13

        field = struct.unpack("<16H", bytes(bytearray(self._usage_binary_data[14:46])))
        self.reg_self_test_5_sense_pins_pin_sense_mask = [*field, ]  # Convert tuple to list

        field0, field1, field2, field3 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[46:54])))
        self.reg_self_test_5_sense_pins_gross_leakage_limit = field0
        self.reg_self_test_5_sense_pins_marginal_leakage_limit = field1
        self.reg_self_test_5_sense_pins_shield_gross_leakage_limit = field2
        self.reg_self_test_5_sense_pins_shield_marginal_leakage_limit = field3

        fields = struct.unpack("<32H", bytes(bytearray(self._usage_binary_data[100:164])))
        for i in range(16):
            self.reg_self_test_8_aux_limits_chan_n_chan_max[i] = fields[i * 2]
            self.reg_self_test_8_aux_limits_chan_n_chan_min[i] = fields[i * 2 + 1]

    def pack(self):
        # Convert the usage binary data into a byte array for struct pack to work
        usage_as_bytearray = bytearray(self._usage_binary_data)

        fields = [0] * 7
        fields[0] = (self.reg_enable_self_test_on_boot & 0x0001)
        fields[0] |= ((self.reg_enable_self_test_on_heartbeat << 1) & 0x0002)
        fields[1] = (self.reg_stop_tests_on_first_error & 0x0001)
        fields[1] |= ((self.reg_enable_u83_self_test_frames << 1) & 0x0002)
        fields[1] |= ((self.reg_fast_self_test_frames_after_reset << 2) & 0x0004)
        fields[1] |= ((self.reg_u83_self_test_every_n_frames << 4) & 0xFFF0)
        fields[2] = (self.reg_u83_self_test_jump & 0xFFFF)
        fields[3] = (self.reg_aux_channels_use_calibration_capacitors & 0x0001)
        fields[3] |= ((self.reg_aux_uses_thermistor << 1) & 0x0002)

        fields[4] = self.reg_run_test_on_boot_0_cpu_ram_test & 0x0001
        fields[4] |= (self.reg_run_test_on_boot_1_ae_baseline_ram_test & 0x0001) << 1
        fields[4] |= (self.reg_run_test_on_boot_2_ae_internal_test & 0x0001) << 2
        fields[4] |= (self.reg_run_test_on_boot_3_vdda_test & 0x0001) << 3
        fields[4] |= (self.reg_run_test_on_boot_4_ae_test & 0x0001) << 4
        fields[4] |= (self.reg_run_test_on_boot_5_sense_and_sheild_pin_leakage_test & 0x0001) << 5
        fields[4] |= (self.reg_run_test_on_boot_9_crc_check_test & 0x0001) << 9
        fields[4] |= (self.reg_run_test_on_boot_11_nvm_test & 0x0001) << 11
        fields[4] |= (self.reg_run_test_on_boot_12_rtc_test & 0x0001) << 12
        fields[4] |= (self.reg_run_test_on_boot_13_vddc_ram_test & 0x0001) << 13

        fields[5] = (self.reg_run_test_on_heartbeat_8_aux_signal_limit_test & 0x0001) << 8
        fields[5] |= (self.reg_run_test_on_heartbeat_9_crc_check_ram_test & 0x0001) << 9
        fields[5] |= (self.reg_run_test_on_heartbeat_10_nirq_pin_test & 0x0001) << 10
        fields[5] |= (self.reg_run_test_on_heartbeat_11_nvm_test & 0x0001) << 11

        fields[6] = (self.reg_run_test_on_host_trigger_1_ae_baseline_ram_test & 0x0001) << 1
        fields[6] |= (self.reg_run_test_on_host_trigger_2_ae_internal_ram_test & 0x0001) << 2
        fields[6] |= (self.reg_run_test_on_host_trigger_3_vdda_test & 0x0001) << 3
        fields[6] |= (self.reg_run_test_on_host_trigger_4_ae_test & 0x0001) << 4
        fields[6] |= (self.reg_run_test_on_host_trigger_5_sense_and_shield_pin_leakage_test & 0x0001) << 5
        fields[6] |= (self.reg_run_test_on_host_trigger_8_aux_signal_limit_test & 0x0001) << 8
        fields[6] |= (self.reg_run_test_on_host_trigger_9_crc_check_test & 0x0001) << 9
        fields[6] |= (self.reg_run_test_on_host_trigger_10_nirq_pin_test & 0x0001) << 10
        fields[6] |= (self.reg_run_test_on_host_trigger_11_nvm_test & 0x0001) << 11
        fields[6] |= (self.reg_run_test_on_host_trigger_13_vddc_test & 0x0001) << 13
        
        struct.pack_into("<7H", usage_as_bytearray, 0, *fields)

        struct.pack_into("<16H", usage_as_bytearray, 14, *self.reg_self_test_5_sense_pins_pin_sense_mask)

        fields = [0] * 4
        fields[0] = (self.reg_self_test_5_sense_pins_gross_leakage_limit & 0xFFFF)
        fields[1] = (self.reg_self_test_5_sense_pins_marginal_leakage_limit & 0xFFFF)
        fields[2] = (self.reg_self_test_5_sense_pins_shield_gross_leakage_limit & 0xFFFF)
        fields[3] = (self.reg_self_test_5_sense_pins_shield_marginal_leakage_limit & 0xFFFF)
        struct.pack_into("<4H", usage_as_bytearray, 46, *fields)

        fields = [0] * 15
        struct.pack_into("<15H", usage_as_bytearray, 54, *fields)

        fields = [0] * 8
        struct.pack_into("<8H", usage_as_bytearray, 84, *fields)

        fields = []
        for i in range(16):
            fields.append(self.reg_self_test_8_aux_limits_chan_n_chan_max[i])
            fields.append(self.reg_self_test_8_aux_limits_chan_n_chan_min[i])
        struct.pack_into("<32H", usage_as_bytearray, 100, *fields)

        # Convert the binary usage data into a list
        self._usage_binary_data = list(usage_as_bytearray)

    def print_registers(self):
        print("u06 Self Tests")
        print("  Enable Self Test on Boot          : %s" % ("Yes" if self.reg_enable_self_test_on_boot else "No"))
        print("  Enable Self Test on Heartbeat     : %s" % ("Yes" if self.reg_enable_self_test_on_heartbeat else "No"))
        print("")
        print("  Stop Self Tests on First Failure  : %s" % ("Yes" if self.reg_stop_tests_on_first_error else "No"))
        print("  Enable u83 Self Test Frames       : %s" % ("Yes" if self.reg_enable_u83_self_test_frames else "No"))
        print("  Fast Self Test Frames After Reset : %s" % ("Yes" if self.reg_fast_self_test_frames_after_reset else "No"))
        print("  u83 Self Test Every               : %u frames" % self.reg_u83_self_test_every_n_frames)
        print("  u83 Self Test Jump                : %u jump" % self.reg_u83_self_test_jump)
        print("  AUX Channels Use Calibration Caps : %s" % ("Yes" if self.reg_aux_channels_use_calibration_capacitors else "No"))
        print("  AUX Uses Thermistor               : %s" % ("Yes" if self.reg_aux_uses_thermistor else "No"))
        print("")
        print("  Self Test to run on Boot")
        print("    Test  0: CPU RAM Test                 : %s" % ("Yes" if self.reg_run_test_on_boot_0_cpu_ram_test else "No"))
        print("    Test  1: AE Baseline RAM Test         : %s" % ("Yes" if self.reg_run_test_on_boot_1_ae_baseline_ram_test else "No"))
        print("    Test  2: AE Internal Test             : %s" % ("Yes" if self.reg_run_test_on_boot_2_ae_internal_test else "No"))
        print("    Test  3: VDDA Test                    : %s" % ("Yes" if self.reg_run_test_on_boot_3_vdda_test else "No"))
        print("    Test  4: AE Test                      : %s" % ("Yes" if self.reg_run_test_on_boot_4_ae_test else "No"))
        print("    Test  5: Sense and Shield Pin Leakage : %s" % ("Yes" if self.reg_run_test_on_boot_5_sense_and_sheild_pin_leakage_test else "No"))
        print("    Test  9: CRC Check Test               : %s" % ("Yes" if self.reg_run_test_on_boot_9_crc_check_test else "No"))
        print("    Test 11: NVM Test                     : %s" % ("Yes" if self.reg_run_test_on_boot_11_nvm_test else "No"))
        print("    Test 12: RTC Test                     : %s" % ("Yes" if self.reg_run_test_on_boot_12_rtc_test else "No"))
        print("    Test 13: VDDC RAM Test                : %s" % ("Yes" if self.reg_run_test_on_boot_13_vddc_ram_test else "No"))
        print("  Self Test to run on Heartbeat")
        print("    Test  8: AUX Signal Limit Test        : %s" % ("Yes" if self.reg_run_test_on_heartbeat_8_aux_signal_limit_test else "No"))
        print("    Test  9: CRC Check RAM Test           : %s" % ("Yes" if self.reg_run_test_on_heartbeat_9_crc_check_ram_test else "No"))
        print("    Test 10: NIRQ Pin Test                : %s" % ("Yes" if self.reg_run_test_on_heartbeat_10_nirq_pin_test else "No"))
        print("    Test 11: NVM Test                     : %s" % ("Yes" if self.reg_run_test_on_heartbeat_11_nvm_test else "No"))
        print("  Self Test to run on Host Trigger")
        print("    Test  1: AE Baseline RAM Test         : %s" % ("Yes" if self.reg_run_test_on_host_trigger_1_ae_baseline_ram_test else "No"))
        print("    Test  2: AE Internal RAM Test         : %s" % ("Yes" if self.reg_run_test_on_host_trigger_2_ae_internal_ram_test else "No"))
        print("    Test  3: VDDA Test                    : %s" % ("Yes" if self.reg_run_test_on_host_trigger_3_vdda_test else "No"))
        print("    Test  4: AE Test                      : %s" % ("Yes" if self.reg_run_test_on_host_trigger_4_ae_test else "No"))
        print("    Test  5: Sense and Shield Pin Leakage : %s" % ("Yes" if self.reg_run_test_on_host_trigger_5_sense_and_shield_pin_leakage_test else "No"))
        print("    Test  8: AUX Signal Limit Test        : %s" % ("Yes" if self.reg_run_test_on_host_trigger_8_aux_signal_limit_test else "No"))
        print("    Test  9: CRC Check Test               : %s" % ("Yes" if self.reg_run_test_on_host_trigger_9_crc_check_test else "No"))
        print("    Test 10: NIRQ Pin Test                : %s" % ("Yes" if self.reg_run_test_on_host_trigger_10_nirq_pin_test else "No"))
        print("    Test 11: NVM Test                     : %s" % ("Yes" if self.reg_run_test_on_host_trigger_11_nvm_test else "No"))
        print("    Test 13: VDDC Test                    : %s" % ("Yes" if self.reg_run_test_on_host_trigger_13_vddc_test else "No"))
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
        print("  Self Test 8 - AUX Signal Limits")
        print("          " + " ".join(f"{i:5}" for i in range(16)))
        print("    Max : " + " ".join(f"{v:5}" for v in self.reg_self_test_8_aux_limits_chan_n_chan_max))
        print("    Min : " + " ".join(f"{v:5}" for v in self.reg_self_test_8_aux_limits_chan_n_chan_min))
