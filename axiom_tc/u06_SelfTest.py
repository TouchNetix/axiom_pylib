# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import struct
from time import sleep
import logging

from axiom_usages.axiom_usages.usages import u06

logger = logging.getLogger(__name__)

class u06_SelfTest(u06):

    def __init__(self, usage_bytes: bytearray):
        
        self._raw = bytearray(self.USAGE_LEN) 

        self.set_bytes(usage_bytes[:self.USAGE_LEN])

        return

    def print(self):
        self.print_fld_attributes()

    def toggle_heartbeat_tests(self, val):
        self.fld_run_test_6_heartbeat = val
        self.fld_run_test_7_heartbeat = val
        self.fld_run_test_8_heartbeat = val
        self.fld_run_test_9_heartbeat = val
        self.fld_run_test_10_heartbeat = val
        self.fld_enableu83selftestframes = val
        self.fld_enableselftestonheartbeat = val

    def toggle_boot_tests(self, val):
        self.fld_run_test_0_boot = val
        self.fld_run_test_1_boot = val
        self.fld_run_test_2_boot = val
        self.fld_run_test_3_boot = val
        self.fld_run_test_4_boot = val
        self.fld_run_test_5_boot = val
        self.fld_run_test_9_boot = val
        self.fld_run_test_11_boot = val
        self.fld_run_test_12_boot = val
        self.fld_run_test_13_boot = val
        self.fld_enableselftestonboot = val
        
    def toggle_user_trigger_tests(self, val, skip_signal_limit_tests=True):
        self.fld_run_test_1_hosttrigger = val
        self.fld_run_test_2_hosttrigger = val
        self.fld_run_test_3_hosttrigger = val
        self.fld_run_test_4_hosttrigger = val
        self.fld_run_test_5_hosttrigger = val
        self.fld_run_test_9_hosttrigger = val
        self.fld_run_test_10_hosttrigger = val
        self.fld_run_test_11_hosttrigger = val
        self.fld_run_test_13_hosttrigger = val
        if not skip_signal_limit_tests:
            self.fld_run_test_6_hosttrigger = val
            self.fld_run_test_7_hosttrigger = val
            self.fld_run_test_8_hosttrigger = val
