# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import logging

from axiom_usages.axiom_usages.usages import u34


logger = logging.getLogger(__name__)

class u34_ReportController(u34):
    
    def __init__(self, report_data):
        self._raw = report_data

        if self.fld_payloadbuffer_0.repeat_count == 0: 
            self.fld_payloadbuffer_0.set_repeat_count(self.fld_reportlength)

    def get_report(self):

        return self.fld_payloadbuffer_0.get_repeat_bytes()