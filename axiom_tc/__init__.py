# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from .axiom import axiom
from .Bootloader import Bootloader
from .u02_SystemManager import u02_SystemManager
from .u03_SystemControls import u03_SystemControls
from .u06_SelfTest import u06_SelfTest
from .u07_LiveView import u07_LiveView
from .u31_DeviceInformation import u31_DeviceInformation
from .u32_DeviceCapabilities import u32_DeviceCapabilities
from .u33_CRCData import u33_CRCData
from .u48_GPIOControls import u48_GPIOControls
from .u34_ReportController import u34_ReportController

__all__ = [
    "axiom",
    "Bootloader",
    "u02_SystemManager",
    "u03_SystemControls",
    "u06_SelfTest",
    "u07_LiveView",
    "u31_DeviceInformation",
    "u32_DeviceCapabilities",
    "u33_CRCData",
    "u34_ReportController",
    "u48_GPIOControls",
]

try:
    from .USB_Comms import *
    __all__.append("USB_Comms")
except ImportError:
    pass

try:
    from .I2C_Comms import *
    __all__.append("I2C_Comms")
except ImportError:
    pass

try:
    from .SPI_Comms import *
    __all__.append("SPI_Comms")
except ImportError:
    pass
