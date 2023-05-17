# aXiom python library

This library provides users the building blocks to communicate with the aXiom touch controllers. By linking these building blocks together, more complex functions can be acheived, such as loading firmware, loading configuration files or building a production test process.

## File Overview

`axiom.py` - Provides the main business logic and interface to aXiom.

`I2C_Comms.py` - Provides the logic for performing I2C comms to aXiom.

`SPI_Comms.py` - Provides the logic for performing SPI comms to aXiom.

`USB_Comms.py` - Provides the logic for performing USB comms to aXiom.

`CDU_Common.py` - Some usages are CDU (command driven usages). These usages some some additional logic to read/write their contents.

`u02_SystemManager.py` - Provides access to aXiom's system manager. The aXiom device can be reset, jump to bootloader, save config changes to flash etc.

`u06_SelfTest.py` - Provides access to configure and control the self test settings in aXiom.

`u07_LiveView.py` - Provides access to read live data from aXiom. For instance GPIO status, acqusition status and self test status.

`u33_CRCData.py` - Provides access to the CRCs within aXiom.

`uXX_Template.py` - Template file to use when creating more python files for specific usages.

## Prerequisites

### I2C Interface

Requires `smbus2` to be installed and accessible to your Python interpreter.

```console
pip install smbus2
```

See [smbus2](https://pypi.org/project/smbus2/) for more information.


### SPI Interface

Requires `spidev` to be installed and accessible to your Python interpreter.

```console
pip install spidev
```

See [spidev](https://pypi.org/project/spidev/) for more information.

### USB Interface

Requires `hid` to be installed and accessible to your Python interpreter.

```console
pip install hid
```

See [hid](https://pypi.org/project/hid/) for more information.

#### Using hid module on Windows

Windows requires the `hidapi.dll` files to reside in the same directory as python (see more info [here](https://github.com/abcminiuser/python-elgato-streamdeck/issues/56))
The `.dll` files can be found [here](https://github.com/libusb/hidapi/releases)