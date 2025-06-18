# Copyright (c) 2025 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from time import sleep

from .u06_SelfTest_rev3 import u06_SelfTestRev3
from .u06_SelfTest_rev4 import u06_SelfTestRev4
from .u06_SelfTest_rev5 import u06_SelfTestRev5
from .u06_SelfTest_rev6 import u06_SelfTestRev6
from .u06_SelfTest_rev7 import u06_SelfTestRev7


class u06_SelfTest:
    USAGE_ID = 0x06
    _REVISION_MAP = {
        3: u06_SelfTestRev3,
        4: u06_SelfTestRev4,
        5: u06_SelfTestRev5,
        6: u06_SelfTestRev6,
        7: u06_SelfTestRev7,
    }

    def __init__(self, axiom, read=True):
        self._axiom = axiom
        self._usage_revision = self._axiom.get_usage_revision(self.USAGE_ID)
        usage_handler = self._REVISION_MAP.get(self._usage_revision)
        if usage_handler is None:
            raise Exception(f"Unsupported revision of u06 SelfTest: {self._usage_revision}")
        self._usage_handler = usage_handler(axiom, self.USAGE_ID, read)

    def read(self):
        self._usage_handler.read()

    def write(self, write_to_nvm=False):
        self._usage_handler.write(write_to_nvm)

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
