# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import logging

from axiom_usages.axiom_usages.usages import u07

from .UsageManager import UsageManager

logger = logging.getLogger(__name__)

def convert_u83_measurement_noise_to_string(noise_as_float100):
    return "%.2f" % (float(noise_as_float100) / 100)

class u07_LiveView(u07):

    def __init__(self, usage_bytes: bytearray):

        self._raw = bytearray(self.USAGE_LEN) 

        self.set_bytes(usage_bytes[:self.USAGE_LEN])
 
        return

    def print(self, self_test_only=True):
        self._print_flds(self_test_only)

    def _print_flds(self, self_test_only=True):
        if not self_test_only:
            logger.info("u07 Live Data")
            logger.info(f"  AE Running                 : {self.fld_aestatus_run.name}")
            logger.info(f"  AE Clipping                : {self.fld_aestatus_clipping.name}")
            logger.info(f"  Reduced Power Mode         : {self.fld_lpmstate.name}")
            logger.info(f"  Trans Status               : {self.fld_trans_status.name}")
            logger.info(f"  Abs Status                 : {self.fld_abs_status.name}")
            logger.info(f"  Aux Status                 : {self.fld_aux_status.name}")
            logger.info(f"  Large Contact Suppressed   : {self.fld_large_contact_suppressed.name}")
            logger.info(f"  Palm Suppressed            : {self.fld_palm_supressed.name}")
            logger.info(f"  Large Hover Suppressed     : {self.fld_large_hover_supressed.name}")
            logger.info(f"  Trans Drifting             : {'Drifting' if self.fld_trans_drifting_active else 'Not Drifting'}")
            logger.info(f"  Abs Drifting               : {'Drifting' if self.fld_abs_drifting_active else 'Not Drifting'}")
            logger.info(f"  Aux Drifting               : {'Drifting' if self.fld_aux_drifting_active else 'Not Drifting'}")
            logger.info("")

        logger.info("  Self Test Status")
        logger.info(f"    u06 Self Test Status               : {self.fld_u06selftest_status.name}")
        logger.info(f"    u06 Self Test Triggered By         : {self.fld_u06selftest_cause.name}")
        logger.info(f"    u06 Self Test Current Test Running : {self.fld_u06selftest_testnumber}")
        logger.info(f"    u06 Self Test Overall Result       : {self.fld_u06selftest_overallresult.name}")
        logger.info(f"    u06 Self Test Debug Data           : {self.fld_u06selftest_generaldebug}")
        logger.info("")

        logger.info("  Self Test Results")
        result_fields = [
            ("CPU RAM Test", self.fld_cpu_ram_result_0),
            ("AE Baseline RAM Test", self.fld_ae_baseline_ram_result_1),
            ("AE Internal RAM Test", self.fld_ae_internal_ram_result_2),
            ("VDDA Test", self.fld_vdda_result_3),
            ("AE Test", self.fld_ae_result_4),
            ("Sense and Shield Pin Leakage Test", self.fld_sense_and_shield_pins_leakage_result_5),
            ("Abs Cap Signal Limits Test", self.fld_abs_signal_limits_result_7),
            ("AUX Signal Limits Test", self.fld_aux_signal_limits_result_8),
            ("CRC Generate and Check Test", self.fld_crc_generate_and_check_result_9),
            ("nIRQ Pin Test", self.fld_nirq_result_10),
            ("NVM Test", self.fld_nvm_result_11),
            ("RTC Test", self.fld_rtc_result_12),
            ("VDDC Test", self.fld_vddc_result_13)
        ]
        if hasattr(self, "fld_trans_signal_limits_result_6"):
            result_fields += [("Trans Cap Signal Limits Test", self.fld_trans_signal_limits_result_6)]

        for idx, (name, field) in enumerate(result_fields):
            result = field.name
            logger.info(f"    Test {idx+1:2d} {name:<35} : {result}")
        
        if not self_test_only:
            logger.info("")
            logger.info("GPIOs State")
            gpio_states = [
                self.fld_gpio0,
                self.fld_gpio1,
                self.fld_gpio2,
            ]
            if hasattr(self, "fld_gpio3"):
                gpio_states += [type(self).fld_gpio3]
            if hasattr(self, "fld_gpio4"):
                gpio_states += [type(self).fld_gpio4]

            for x, g in enumerate(gpio_states):
                logger.info(f" GPIO {x} : {g}")

            logger.info(f"AE Frame Rate")
            logger.info(f"  Current Frame Rate: {self.fld_currentframerate} Hz")
