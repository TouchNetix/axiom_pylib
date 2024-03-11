# aXiom python library

This library provides users the building blocks to communicate with the aXiom touch controllers. By linking these building blocks together, more complex functions can be achieved, such as loading firmware, loading configuration files or building a production test process.

## File Overview

`axiom.py` - Provides the main business logic and interface to aXiom.

`Bootloader.py` - Manages the logic for handling firmware updates.

`I2C_Comms.py` - Provides the logic for performing I2C comms to aXiom.

`SPI_Comms.py` - Provides the logic for performing SPI comms to aXiom.

`USB_Comms.py` - Provides the logic for performing USB comms to aXiom.

`CDU_Common.py` - Some usages are CDU (command driven usages). These usages use additional logic to read/write their contents.

`u02_SystemManager.py` - Provides access to aXiom's system manager. The aXiom device can be reset, jump to bootloader, save config changes to flash etc.

`u06_SelfTest.py` - Provides access to configure and control the self test settings in aXiom.

`u07_LiveView.py` - Provides access to read live data from aXiom. For instance GPIO status, acquisition status and self test status.

`u32_DeviceCapabilities.py` - Reports the capabilities of the aXiom device. For instance, the number CTS nodes, which comms interfaces are supported etc.

`u33_CRCData.py` - Provides access to the CRCs within aXiom.

`u48_GPIOControls.py` - Provides access to the GPIO controls for aXiom.

`uXX_Template.py` - Template file to use when creating more python files for specific usages.

## Prerequisites

Requires Python 3.8 to be installed and accessible on the Path variable.

### axiom_tc Package

This is the aXiom touch controller python package that provides access to core functionality and communication to the aXiom device. In conjunction with the `axiom_tc` package, the appropriate interface packages are expected to be available. These are described after this section.

Requires `axiom_tc` to be installed and accessible to your Python interpreter.

```console
pip install axiom_tc
```

### SPI Interface

Requires `spidev` to be installed and accessible to your Python interpreter.

```console
pip install spidev
```

See [spidev](https://pypi.org/project/spidev/) for more information.

### I2C Interface

Requires `smbus2` to be installed and accessible to your Python interpreter.

```console
pip install smbus2
```

See [smbus2](https://pypi.org/project/smbus2/) for more information.

### USB Interface

Requires `hid` to be installed and accessible to your Python interpreter.

```console
pip install hid==1.0.4
```

See [hid](https://pypi.org/project/hid/) for more information.

#### Linux

Using the `hid` package will access the TouchNetix protocol bridges via the `/dev/hidrawX` interface. This typically requires root access. This means the scripts will need to be run as `sudo`. Alternatively, `udev` can be used to give all users permissions to the `hidraw` devices.

Create the following `udev` rules file `/etc/udev/rules.d/99-axiom-hidraw-permissions.rules`:

```text
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="03eb", ATTRS{idProduct}=="6f02", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="03eb", ATTRS{idProduct}=="2f04", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="03eb", ATTRS{idProduct}=="2f08", MODE="0666"

SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="6f02", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="2f04", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="2f08", MODE="0666"

SUBSYSTEM=="hidraw", ATTRS{idVendor}=="28e9", ATTRS{idProduct}=="6f02", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="28e9", ATTRS{idProduct}=="2f04", MODE="0666"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="28e9", ATTRS{idProduct}=="2f08", MODE="0666"
```

The changes will apply on the next reboot. To apply the changes immediately:

```console
sudo udevadm control --reload-rules
sudo udevadm trigger
```

If this error message is observed:

```console
ImportError: Unable to load any of the following libraries:libhidapi-hidraw.so libhidapi-hidraw.so.0 libhidapi-libusb.so libhidapi-libusb.so.0 libhidapi-iohidmanager.so libhidapi-iohidmanager.so.0 libhidapi.dylib hidapi.dll libhidapi-0.dll
```

Run the following to install the `hidapi` library.

```console
sudo apt-get install libhidapi-hidraw0 libhidapi-libusb0
```

#### Windows

Windows requires the `hidapi.dll` files to reside in the same directory as python (see more info [here](https://github.com/abcminiuser/python-elgato-streamdeck/issues/56))
The `.dll` files can be found [here](https://github.com/libusb/hidapi/releases)

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.