# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import hid
import sys


def byte2ascii(buffer):
    new_buffer = []
    for byte in buffer:
        new_buffer.append("0x%x" % byte)
    return new_buffer


def byte2int(buffer):
    new_buffer = []
    for byte in buffer:
        new_buffer.append(int(byte))
    return new_buffer


class USB_Comms:
    # aXiom specific communication protocol constants
    AX_COMMS_READ = 0x80
    AX_HEADER_LEN = 0x4
    AX_USB_HEADER_LEN = 0x3
    AX_RX_HEADER_LEN = 0x2

    # USB Bridge Specific constants
    MAX_WR_BUFFER_SIZE = 513
    wMaxPacketSize = 64
    hidPayloadSize = wMaxPacketSize + 1

    # TNx Touch-Bridge-Protocol Commands
    # For more details, refer to the relevant protocol bridge datasheet
    AX_TBP_CMD_NULL = 0x86
    AX_TBP_I2C_DEVICE1 = 0x51  # Read as: issue i2c/SPI transaction to device 1.
    AX_TBP_I2C_DEVICE2 = 0x52  # Read as: issue i2c/SPI transaction to device 2.
    AX_TBP_REPEAT = 0x88  # a.k.a. "put bridge in proxy mode".
    AX_TBP_USBID_UNSOLICITED = 0x9A  # "unsolicited" report from the bridge when in Proxy Mode.
    AX_CMD_RESET = 0xEF

    # Maximum payload size for USB bridge commands 0x51 and 0x52
    AX_TBP_I2C_DEV_HEAD_LEN = 3

    # Following constants are responses when issuing either:
    # * AX_TBP_I2C_DEVICE1
    # * AX_TBP_I2C_DEVICE2
    #
    # requests. These id's will be the first byte of the response.
    AX_TBP_RDWR_OK = 0x0
    AX_TBP_NOACK_DATA = 0x1
    AX_TBP_NOACK_ADDR = 0x2
    AX_TBP_WR_OK = 0x4

    # USB Interface numbers
    AX_IF_TBPCTRL = 0x0  # TBP Control Interface
    AX_IF_DIGITIZER = 0x1  # Digitizer Interface
    AX_IF_FORCEDATA = 0x2  # Press Data Interface

    ATMEL_VENDOR_ID = 0x03EB
    ST_VENDOR_ID = 0x0483
    GD_VENDOR_ID = 0x28E9
    VENDOR_ID = [ATMEL_VENDOR_ID, ST_VENDOR_ID, GD_VENDOR_ID]
    PRODUCT_ID = [0x6f02, 0x2f04, 0x2f08]
    EMPTY_PKT = [0] * MAX_WR_BUFFER_SIZE
    RD_TIMEOUT = 100
    MAX_TBP_STOP_RETRY = 2

    def __init__(self, verbose=False):
        self._axiom = None
        # Check for a connected bridge
        # If multiple bridges are connected, the priority is as follows:
        # ATMEL -> ST -> GD
        for VID in self.VENDOR_ID:
            usb_devices = hid.enumerate(VID)
            self.max_length = 0
            self._verbose = verbose
            if len(usb_devices) != 0:
                # USB Bridge found
                break

        # usb_devices will be empty here if we didn't find any USB bridges
        if len(usb_devices) == 0:
            print("ERROR: Did not find a Protocol Bridge.")
            sys.exit(1)

        else:
            if self._verbose:
                print("Found TNx USB Bridge devices...")
            for dev in usb_devices:
                # Graceful error needed for USB device not available
                if dev['interface_number'] == self.AX_IF_TBPCTRL:
                    path = dev['path']
                    self.__device = hid.Device(path=path)
                    self.vid = dev['vendor_id']
                    self.pid = dev['product_id']

                    if self._verbose:
                        print('    Grabbing device in path: ', path)
                        print('    Manufacturer String:     ', dev['manufacturer_string'])
                        print('    Product String:          ', dev['product_string'])
                        print('    Vendor ID:  0x%4x' % self.vid)
                        print('    Product ID: 0x%4x' % self.pid)

                    # TODO: Max Length needs to be taken from End-Point's descriptor
                    # self.max_length = self.__device.get_indexed_string(1, max_length=10)
                    if 'TNxPB-005' in dev['product_string']:
                        self.wMaxPacketSize = 512
                    if 'TNxPB-007' in dev['product_string']:
                        self.wMaxPacketSize = 64
                    if 'AXPB009' in dev['product_string']:
                        self.wMaxPacketSize = 64

                    self.hidPayloadSize = self.wMaxPacketSize + 1
                    self.max_wr_pay_length = (self.wMaxPacketSize == 64) and (
                                64 - self.AX_HEADER_LEN - self.AX_USB_HEADER_LEN) or (255 - self.AX_HEADER_LEN)
                    self.max_rd_pay_length = (self.wMaxPacketSize == 64) and (64 - self.AX_RX_HEADER_LEN) or 255
                    if self._verbose:
                        print('Max Write Length: ' + str(self.max_wr_pay_length))
                        print('Max Read Length: ' + str(self.max_rd_pay_length))
            try:  # Fail gracefully if the USB object can't be acquired
                if self.__device:
                    pass
            except AttributeError:
                print("ERROR: USB device could not be acquired. The device might already in use.")
                sys.exit(1)

    def stop_bridge(self):
        if self._verbose:
            print("    Stopping Proxy Mode...")
        buffer_wr = list(self.EMPTY_PKT)
        buffer_wr[1] = self.AX_TBP_CMD_NULL

        # See the following:
        # https://github.com/sergiomsilva/alpr-unconstrained/issues/73
        # For the reason of having to use the "bytes" function
        self.__device.write(bytes(buffer_wr[0:self.hidPayloadSize]))
        if self._verbose:
            print("    Bridge Stop requested...")

        # Check for buffer, if they don't match, just try a couple of times:
        retries = 0
        while retries < self.MAX_TBP_STOP_RETRY:
            buffer_rd = self.__device.read(self.hidPayloadSize, timeout=self.RD_TIMEOUT)
            if self._verbose:
                print(buffer_rd)

            if buffer_rd[0] == self.AX_TBP_CMD_NULL:
                while len(buffer_rd) != 0:
                    buffer_rd = self.__device.read(self.hidPayloadSize, timeout=self.RD_TIMEOUT)
                if self._verbose:
                    print("    flushed...")
                return
        print("ERROR: could not issue stop command to USB Bridge.")
        raise AssertionError

    def comms_init(self, axiom):
        self._axiom = axiom
        self.stop_bridge()

    def read_page(self, target_address, length):
        # if length > (self.max_rd_pay_length):
        #    print("ERROR: Asked to read more bytes than available in payload: ")
        #    print("Requested length: %d, allowed is %d" % (length, self.max_rd_pay_length))
        #    raise ValueError

        if self._verbose:
            print("\nUSB Read request at add: 0x%x, length: %d" % (target_address, length))

        left_to_transfer = length
        to_address = target_address

        ret_buffer = []

        while left_to_transfer > 0:

            if left_to_transfer >= self.max_rd_pay_length:
                to_transfer = self.max_rd_pay_length
                left_to_transfer = left_to_transfer - self.max_rd_pay_length
                ta_msb = (to_address & 0xFF00) >> 8
                ta_lsb = (to_address & 0x00FF)
                if self._verbose:
                    print("Address 0x%x" % to_address)
                to_address = to_address + to_transfer

            else:
                to_transfer = left_to_transfer
                left_to_transfer = 0
                ta_msb = (to_address & 0xFF00) >> 8
                ta_lsb = (to_address & 0x00FF)

            length_msb = (to_transfer & 0x7F00) >> 8
            length_lsb = (to_transfer & 0x00FF)

            length_msb |= self.AX_COMMS_READ  # Set the READ bit

            usb_header = [0x00, self.AX_TBP_I2C_DEVICE1, self.AX_HEADER_LEN, to_transfer]
            payload_header = [ta_lsb, ta_msb, length_lsb, length_msb]
            message = usb_header + payload_header
            wr_buffer = message + ([0] * (self.hidPayloadSize - len(message)))
            if self._verbose:
                print("Reading from device...")
                print("rd usb_header: ", byte2ascii(usb_header))
                print("rd payload_header: ", byte2ascii(payload_header))
                # print("message: ", message)
                # print("write %d chars to device..." % len(wr_buffer))
            self.__device.write(bytes(wr_buffer))
            rd_buffer = self.__device.read(self.hidPayloadSize, timeout=self.RD_TIMEOUT)
            assert rd_buffer[0] == self.AX_TBP_RDWR_OK
            assert rd_buffer[1] == to_transfer
            if self._verbose:
                print("Device Response:")
                print("rd Buffer is of length: " + str(len(rd_buffer)))
                print("rd Left to transfer: " + str(left_to_transfer))
                print(byte2ascii(rd_buffer[2:2 + to_transfer]))

            ret_buffer = ret_buffer + byte2int(rd_buffer[2:2 + to_transfer])

        if len(ret_buffer) != length:
            print("ERROR: Did not return enough bytes, requested %d, returned %d." %
                  (length, len(ret_buffer)))
            raise AssertionError
        if self._verbose:
            print("returning buffer ", byte2ascii(ret_buffer))
        return list(ret_buffer)

    def write_page(self, target_address, length, payload):
        if length > len(payload):
            print("ERROR: Asked to write more bytes than available in payload: ")
            print("Length: %d, and given payload is %d" % (length, len(payload)))
            raise AssertionError

        if self._verbose:
            print("\nUSB Write request at add: 0x%x, length: %d" % (target_address, length))
            print("payload: ", byte2ascii(payload))

        left_to_transfer = length
        to_address = target_address
        transferred = 0
        while left_to_transfer > 0:

            if left_to_transfer >= self.max_wr_pay_length:
                to_transfer = self.max_wr_pay_length
                left_to_transfer = left_to_transfer - self.max_wr_pay_length
                ta_msb = (to_address & 0xFF00) >> 8
                ta_lsb = (to_address & 0x00FF)
                to_address = to_address + to_transfer

            else:
                to_transfer = left_to_transfer
                left_to_transfer = 0
                ta_msb = (to_address & 0xFF00) >> 8
                ta_lsb = (to_address & 0x00FF)

            length_msb = (to_transfer & 0x7F00) >> 8
            length_lsb = (to_transfer & 0x00FF)

            # Ensure the read bit is clear
            # NOTE: Python does not do bit-wise not. Here we
            #       subtract from 0xff to achieve that.
            # credit to:
            #     https://stackoverflow.com/questions/31151107/how-do-i-do-a-bitwise-not-operation-in-python
            length_msb &= 0xFF - self.AX_COMMS_READ

            usb_header = [0x00, self.AX_TBP_I2C_DEVICE1, to_transfer + self.AX_HEADER_LEN, 0x0]
            payload_header = [ta_lsb, ta_msb, length_lsb, length_msb]
            message = usb_header + payload_header + payload[transferred:transferred + to_transfer]
            buffer = message + ([0] * (self.hidPayloadSize - len(message)))
            if self._verbose:
                print("Writing %d bytes to device..." % to_transfer)
                print("wr usb_header: ", byte2ascii(usb_header))
                print("wr payload_header: ", byte2ascii(payload_header))
                # print("payload: ", byte2ascii(payload))
                print("message: ", byte2ascii(message))
                # print("len(buffer): %d, to_transfer: %d" % (len(buffer),to_transfer))
            assert len(buffer) == self.hidPayloadSize
            self.__device.write(bytes(buffer))
            rd_buffer = self.__device.read(self.hidPayloadSize, timeout=self.RD_TIMEOUT)
            assert rd_buffer[0] == self.AX_TBP_WR_OK
            transferred = transferred + to_transfer

    def read_device(self):
        return self.__device.read(self.hidPayloadSize, timeout=self.RD_TIMEOUT)

    def write_device(self, buffer):
        # See the following:
        # https://github.com/sergiomsilva/alpr-unconstrained/issues/73
        # For the reason of having to use the "bytes" function
        self.__device.write(bytes(buffer[0:self.hidPayloadSize]))

    def set_proxy_mode(self):
        if self._verbose:
            print("Setting USB bridge into Proxy Mode")
        target_address = self._axiom.u31.convert_usage_to_target_address(0x34, 0)
        max_report_len = self._axiom.u31.max_report_len
        if self._verbose:
            print("target address: ", target_address)
            print("max_report_len", max_report_len)
        usb_header = [0x00, self.AX_TBP_REPEAT, 0x58, 0x04]
        payload_header = [max_report_len, target_address & 0xff, target_address >> 8, max_report_len,
                          self.AX_COMMS_READ]
        buffer = usb_header + payload_header + ([0] * (self.hidPayloadSize - len(usb_header) - len(payload_header)))
        self.__device.write(bytes(buffer[0:self.hidPayloadSize]))
        rd_buffer = self.__device.read(self.hidPayloadSize, timeout=self.RD_TIMEOUT)
        assert ((rd_buffer[0] == self.AX_TBP_REPEAT and rd_buffer[1] == self.AX_TBP_RDWR_OK) or  # PB-005
                (rd_buffer[0] == self.AX_TBP_USBID_UNSOLICITED and rd_buffer[1] == 0x4))  # PB-007
        if self._verbose:
            print("Bridge is in Proxy Mode!")

    def reset_bridge(self):
        print("Reset USB bridge")
        buffer = list(self.EMPTY_PKT)
        buffer[1] = self.AX_CMD_RESET
        self.__device.write(bytes(buffer[0:self.hidPayloadSize]))
        # There is no response, the bridge will be soft reset and re-enumerate on the USB bus

    def send_null(self):
        buffer_wr = list(self.EMPTY_PKT)
        buffer_wr[1] = 0x0
        self.write_device(buffer_wr)
        if self._verbose:
            print("    Null Command Sent...")

    def close(self, doreset=False):
        if self.pid == self.PRODUCT_ID[0]:
            # Only do this for tbp mode...
            self.set_proxy_mode()
        else:
            if doreset:
                self.reset_bridge()
            else:
                self.send_null()
        self.__device.close()
