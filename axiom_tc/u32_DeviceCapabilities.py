# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import struct
import logging

from axiom_usages.axiom_usages.usages import u32

logger = logging.getLogger(__name__)

class u32_DeviceCapabilities(u32):

    def __init__(self, usage_bytes: bytearray):
        
        self._raw = bytearray(self.USAGE_LEN) 

        self.set_bytes(usage_bytes[:self.USAGE_LEN])

        return

    def print(self):
        self._print_flds()

    def _print_flds(self):
        logger.info("u32 Device Capabilities:")
        logger.info(f"  Max CTS Nodes         : {self.fld_maxctsnodes}")
        logger.info(f"  Num CTS Channels      : {self.fld_numctschannels}")
        logger.info(f"  Num AUX Channels      : {self.fld_numauxchannels}")
        logger.info(f"  Num CTS Driven Traces : {self.fld_numctsdrivenshields}")
        logger.info(f"  Num AUX Driven Traces : {self.fld_numauxdrivenshields}")
        logger.info(f"  Num A Channels        : {self.fld_numachannels}")
        logger.info(f"  Num B Channels        : {self.fld_numbchannels}")
        logger.info(f"  Num C Channels        : {self.fld_numcchannels}")
        logger.info(f"  Num D Channels        : {self.fld_numdchannels}")
        logger.info(f"  Num E Channels        : {self.fld_numechannels}")
        logger.info(f"  Max Map Length        : {self.fld_maxmaplengthbytes} bytes")
        logger.info(f"  Max Baseline Length   : {self.fld_maxbaselinelengthbytes} bytes")
        logger.info(f"  Num Baselines         : {self.fld_numbaselines}")

        logger.info(f"  Slave I2C             : {'Supported' if self.fld_slavei2c.value == 1 else 'Not Supported'}")
        logger.info(f"  Slave SPI             : {'Supported' if self.fld_slavespi.value == 1 else 'Not Supported'}")
        logger.info(f"  Slave LIN             : {'Supported' if self.fld_slavelin.value == 1 else 'Not Supported'}")
        logger.info(f"  Slave USB             : {'Supported' if self.fld_slaveusb.value == 1 else 'Not Supported'}")
        logger.info(f"  Slave UART            : {'Supported' if self.fld_slaveuart.value == 1 else 'Not Supported'}")
        logger.info(f"  IRQ Notify            : {'Supported' if self.fld_irq.value == 1 else 'Not Supported'}")
        logger.info(f"  External Sync         : {'Supported' if self.fld_extsync.value == 1 else 'Not Supported'}")
        logger.info(f"  Master I2C            : {'Supported' if self.fld_masteri2c.value == 1 else 'Not Supported'}")
        logger.info(f"  Master SPI            : {'Supported' if self.fld_masterspi.value == 1 else 'Not Supported'}")
        logger.info(f"  Master GPIO           : {'Supported' if self.fld_mastergpio.value == 1 else 'Not Supported'}")

        logger.info(f"  Num User GPIOs        : {self.fld_numusergpio}")
        logger.info(f"  KHz to Jump           : {self.fld_khz_to_jump_multiplier} (thousands)")
