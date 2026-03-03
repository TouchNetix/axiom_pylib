# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import logging
from enum import Enum

from axiom_usages.axiom_usages.usages import u48

logger = logging.getLogger(__name__)

class u48_GPIOControls(u48):

    def __init__(self, usage_bytes: bytearray):

        self._raw = bytearray(self.USAGE_LEN) 

        self.set_bytes(usage_bytes[:self.USAGE_LEN])
 
        self._gpio_fields = [
            type(self).fld_gpio0,
            type(self).fld_gpio1,
            type(self).fld_gpio2,
        ]
        if hasattr(self, "fld_gpio3"):
            self._gpio_fields += [type(self).fld_gpio3]
        if hasattr(self, "fld_gpio4"):
            self._gpio_fields += [type(self).fld_gpio4]

    def print(self):
        logger.info("u48 GPIO Controls:")

        for pin, fld in enumerate(self._gpio_fields):
            val = getattr(self, fld.name)
            logger.info(f"GPIO {pin}: {val}")

    def set_gpio(self, gpio: int, val: int | Enum):
        # Check GPIO index is valid
        if gpio not in range(len(self._gpio_fields)):
            raise ValueError(f"Unsupported GPIO index {gpio}!")

        # Write the value directly to the corresponding Field
        fld = self._gpio_fields[gpio]
        setattr(self, fld.name, val)
        