# Copyright (c) 2025 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from .u07_LiveView_rev13 import u07_LiveViewRev13

class u07_LiveViewRev14(u07_LiveViewRev13):
    """
    u07 Live View Revision 14: Functionally identical to Revision 13, but specific to AX198A.
    The only difference is that for Test 2 (AE Internal RAM test), Revision 14 provides an
    additional error code in the extended error bits.

    For more details, see the aXiom Programmer's Guide (TNxAN00060 or TNxAN00094).
    """
    def __init__(self, axiom, usage_id, read=True):
        super().__init__(axiom, usage_id, read=False)

    def _init_registers(self):
        super()._init_registers()

    def unpack(self):
        super().unpack()

    def print_registers(self):
        super().print_registers()
