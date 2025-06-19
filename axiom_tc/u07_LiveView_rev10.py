# Copyright (c) 2025 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from .u07_LiveView_rev9 import u07_LiveViewRev9
class u07_LiveViewRev10(u07_LiveViewRev9):
    """
    u07 Live View Revision 10: Functionally identical to Revision 9, but specific to AX198A.
    The only difference is that for Test 2 (AE Internal RAM test), Revision 10 provides an
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
