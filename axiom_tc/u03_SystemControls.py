# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import struct
from time import sleep
import logging

from axiom_usages.axiom_usages.usages import u03
    
logger = logging.getLogger(__name__)

class u03_SystemControls(u03):

    def __init__(self, usage_bytes: bytearray):
        
        self._raw = bytearray(self.USAGE_LEN) 

        self.set_bytes(usage_bytes[:self.USAGE_LEN])

        return
        
    def print(self):
        self.print_fld_attributes()
    
    def get_hb_period(self):
        return self.fld_heartbeatperiodmult * 0.1 + 0.1 # heartbeat period in seconds