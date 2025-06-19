# Copyright (c) 2025 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from .u07_LiveView_rev6  import u07_LiveViewRev6
from .u07_LiveView_rev7  import u07_LiveViewRev7
from .u07_LiveView_rev8  import u07_LiveViewRev8
from .u07_LiveView_rev9  import u07_LiveViewRev9
from .u07_LiveView_rev10 import u07_LiveViewRev10
from .u07_LiveView_rev11 import u07_LiveViewRev11
from .u07_LiveView_rev12 import u07_LiveViewRev12
from .u07_LiveView_rev13 import u07_LiveViewRev13
from .u07_LiveView_rev14 import u07_LiveViewRev14

class u07_LiveView:
    USAGE_ID = 0x07
    _REVISION_MAP = {
        6:  u07_LiveViewRev6,
        7:  u07_LiveViewRev7,
        8:  u07_LiveViewRev8,
        9:  u07_LiveViewRev9,
        10: u07_LiveViewRev10,
        11: u07_LiveViewRev11,
        12: u07_LiveViewRev12,
        13: u07_LiveViewRev13,
        14: u07_LiveViewRev14,
    }

    def __init__(self, axiom, read=True):
        self._axiom = axiom
        self._usage_revision = self._axiom.get_usage_revision(self.USAGE_ID)
        usage_handler = self._REVISION_MAP.get(self._usage_revision)
        if usage_handler is None:
            raise Exception(f"Unsupported revision of u07 Live View: {self._usage_revision}")
        self._usage_handler = usage_handler(axiom, self.USAGE_ID, read)

    def read(self):
        self._usage_handler.read()

    def write(self, write_to_nvm=False):
        raise PermissionError("u07_LiveView is read-only and does not support write operations.")

    def print(self):
        self._usage_handler.print()

    def __getattr__(self, name):
        try:
            return getattr(self._usage_handler, name)
        except AttributeError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in ("_axiom", "_usage_revision", "_usage_handler", "USAGE_ID", "_REVISION_MAP"):
            super().__setattr__(name, value)
        else:
            setattr(self._usage_handler, name, value)
