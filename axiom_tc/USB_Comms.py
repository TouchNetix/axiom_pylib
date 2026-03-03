# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import time
import hid
import sys
import logging
from enum import IntEnum

logger = logging.getLogger(__name__)

def byte2ascii(buffer):
    return [f"0x{byte:02X}" for byte in buffer]

def byte2int(buffer):
    new_buffer = []
    for byte in buffer:
        new_buffer.append(int(byte))
    return new_buffer

def split_word(word):
    msb = (word & 0xFF00) >> 8
    lsb = (word & 0x00FF)
    return msb, lsb

class TBPBridge(IntEnum):
    CMD_ENTER_BOOTLOADER = 0xF5
    CMD_RESET_BRIDGE = 0xEF
    CMD_FIND_I2C_ADDRESS = 0xE0
    CMD_SWITCH_MODE_TBP_BASIC = 0xFA
    CMD_SWITCH_MODE_TBP_DIGITIZER = 0xFE
    CMD_SWITCH_MODE_TBP_ABS_MOUSE = 0xFF
    CMD_GET_BRIDGE_MODE = 0xF9
    CMD_BLOCK_DIGITIZER_REPORTS = 0x87
    CMD_BLOCK_PRESS_REPORTS = 0xB1

class TBP(IntEnum):
    # Control / Command IDs (from AXPB009 datasheet)
    CMD_ZERO = 0x00
    CMD_AXIOM_COMMS = 0x51
    CMD_MULTIPAGE_READ = 0x71
    CMD_START_PROXY = 0x88
    CMD_NULL = 0x86
    CMD_BLOCK_PRESS_REPORTS = 0xB1
    CMD_WRITE_USAGE = 0xA2
    CMD_READ_USAGE = 0xA3
    CMD_RESET_AXIOM = 0x99


class USB_Comms:
    COMMS_TYPE = "USB"

    # aXiom specific communication protocol constants
    AX_COMMS_READ = 0x80
    AX_HEADER_LEN = 0x4
    AX_USB_HEADER_LEN = 0x3
    AX_RX_HEADER_LEN = 0x2

    # USB Bridge Specific constants
    MAX_WR_BUFFER_SIZE = 513

    # TNx Touch-Bridge-Protocol Commands
    # For more details, refer to the relevant protocol bridge datasheet
    AX_TBP_CMD_NULL = 0x86
    AX_TBP_I2C_DEVICE1 = 0x51  # Read as: issue i2c/SPI transaction to device 1.
    AX_TBP_I2C_DEVICE2 = 0x52  # Read as: issue i2c/SPI transaction to device 2.
    AX_TBP_USBID_UNSOLICITED = 0x9A  # "unsolicited" report from the bridge when in Proxy Mode.

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
    TNX_VENDOR_ID = 0x3825
    VENDOR_ID = [ATMEL_VENDOR_ID, ST_VENDOR_ID, GD_VENDOR_ID, TNX_VENDOR_ID]
    PRODUCT_ID = [0x6f02, 0x2f04, 0x2f08]
    MAX_TBP_RETRY = 3
    report_id = 0x00  # Default report ID for the USB Bridge
    rd_base = 0

    def __init__(self):
        self._device_connected = False
        self._device = hid.device()
        # Check for a connected bridge
        # If multiple bridges are connected, the priority is as follows:
        # ATMEL -> ST -> GD
        for VID in self.VENDOR_ID:
            usb_devices = hid.enumerate(VID)
            self.max_length = 0
            if len(usb_devices) != 0:
                # USB Bridge found
                break

        # usb_devices will be empty here if we didn't find any USB bridges
        if len(usb_devices) == 0:
            logger.error("Did not find a Protocol Bridge.")
            sys.exit(1)

        logger.debug("Found TNx USB Bridge devices...")
        for dev in usb_devices:
            try:
                # For PB014, use digitizer interface (1), for others use control interface (0)
                product_str = dev.get('product_string', '')
                if 'AXPB014' in product_str:
                    target_interface = self.AX_IF_DIGITIZER  # Interface 1 for PB014
                else:
                    target_interface = self.AX_IF_TBPCTRL    # Interface 0 for others
                
                if dev['interface_number'] == target_interface:
                    path = dev['path']
                    self._device.open_path(path)
                    self._device.set_nonblocking(True)
                    
                    self.vid = dev['vendor_id']
                    self.pid = dev['product_id']

                    logger.debug(f'    Grabbing device in path: {path}')
                    logger.debug(f'    Manufacturer String:     {dev["manufacturer_string"]}')
                    logger.debug(f'    Product String:          {dev["product_string"]}')
                    logger.debug(f'    Vendor ID:  0x{self.vid:4x}')
                    logger.debug(f'    Product ID: 0x{self.pid:4x}')

                    self.bridge_type = None
                    # Set packet size based on product name
                    product = dev['product_string']
                    if 'TNxPB-005' in product:
                        self.w_max_packet_size = 512
                        self.bridge_type = 'AXPB005'
                    elif 'TNxPB-007' in dev['product_string']:
                        self.w_max_packet_size = 64
                        self.bridge_type = 'AXPB007'
                    elif 'AXPB009' in dev['product_string']:
                        self.w_max_packet_size = 64
                        self.bridge_type = 'AXPB009'
                    elif 'AXPB011' in dev['product_string']:
                        self.w_max_packet_size = 64
                        self.bridge_type = 'AXPB011'
                    elif 'AXPB014' in dev['product_string']:
                        self.w_max_packet_size = 64
                        self.bridge_type = 'AXPB014'
                    elif 'AXPB015' in dev['product_string']:
                        self.w_max_packet_size = 64
                        self.bridge_type = 'AXPB015'
                        self.rd_base = 1 # account for report id in read payload
                        self.report_id = 1
                    else:
                        logging.warning(f"Unrecognised bridge! name: {product}")
                        self.w_max_packet_size = 64  # default fallback


                    if self.w_max_packet_size == 64:
                        self.max_wr_pay_length = 64 - self.AX_HEADER_LEN - self.AX_USB_HEADER_LEN
                        self.max_rd_pay_length = 64 - self.AX_RX_HEADER_LEN
                    else:
                        self.max_wr_pay_length = 255 - self.AX_HEADER_LEN
                        self.max_rd_pay_length = 255

                    # There is 1 less payload byte when report id is used
                    if self.report_id != 0:
                        self.hid_payload_size = self.w_max_packet_size
                        self.max_wr_pay_length -= 1
                        self.max_rd_pay_length -= 1
                    else:
                        self.hid_payload_size = self.w_max_packet_size + 1

                    logger.debug('Max Write Length: ' + str(self.max_wr_pay_length))
                    logger.debug('Max Read Length: ' + str(self.max_rd_pay_length))

                    self._device_connected = True
                    break

            except Exception as e:
                logger.error(f"Could not acquire device: {e}")
                sys.exit(1)

        # Verify device opened
        if not self._device_connected:
            logger.error("USB device could not be acquired. The device might already be in use.")
            sys.exit(1)
        else:
            logger.info("USB Bridge connected successfully!")
        
    def stop_bridge(self):
        logger.debug("Stopping Proxy Mode...")

        stop_ack = False
        for i in range(10):
            self.write(TBP.CMD_NULL, bytearray(), report_id=self.report_id)
            logger.debug("Bridge Stop requested...")

            stop_retry = 30 # the read buffer can be full of reports, so it needs to be emptied
            for _ in range(stop_retry):
                rd = self.read(TBP.CMD_NULL, ignore_response=True, timeout_ms=200)
                if len(rd) > 0:
                    stop_ack = True
                    break

            if stop_ack:
                if self.flush_buffer():
                    break
        else:  
            raise AssertionError("Could not issue stop command to USB Bridge!")


        
    def comms_init(self):
        self.stop_bridge()    
        self.get_device_mode()

    def read(self, response_id=None, ignore_response=False, timeout_ms=100) -> bytearray: 
        buffer = bytearray()

        start_time = time.time()
        while time.time() < start_time + (timeout_ms / 1000.0):
            buffer = bytearray(self._device.read(self.hid_payload_size))
            if buffer:
                break
        else:
            if not ignore_response:
                logging.error("Timeout reading from aXiom bridge!")

            return bytearray()
        
        
        if response_id != None:
            if buffer[self.rd_base] != response_id:
                if not ignore_response:
                    logging.error(f"Unexpected response id: {buffer[self.rd_base]}!")         

                return bytearray()
            
        return buffer[self.rd_base + 1:]
    
    def write(self, cmd_type: TBP | TBPBridge, payload: bytearray, report_id=0):
        if len(payload) > self.hid_payload_size - 2:
            raise ValueError("Write operation too long!") 

        assert isinstance(payload, bytearray), "payload must be bytearray!"

        buffer = bytearray(self.hid_payload_size)
        
        buffer[0:2] = bytearray([report_id, cmd_type])

        buffer[2:2+len(payload)] = payload

        self._device.write(bytes(buffer))

    def read_page(self, target_address, length, ignore_return=False):
        logger.debug(f"USB Read request at address: 0x{target_address:x}, length: {length}")

        page_buffer = bytearray(length)  # preallocate the full page buffer
        left_to_transfer = length
        read_address = target_address
        offset = 0  # current write offset in page_buffer

        while left_to_transfer > 0:
            # determine chunk size
            rx_bytes = min(left_to_transfer, self.max_rd_pay_length)
            left_to_transfer -= rx_bytes

            addr_msb, addr_lsb = split_word(read_address)

            length_msb, length_lsb = split_word(rx_bytes)
            length_msb |= self.AX_COMMS_READ  # set READ bit

            tx_bytes = 4 # hardcoded for CMD_AXIOM_COMMS read, see datasheet
            payload = bytearray([tx_bytes, rx_bytes, addr_lsb, addr_msb, length_lsb, length_msb])

            logger.debug(f"Reading from address 0x{read_address:04x} with length {rx_bytes}")
            logger.debug(f"payload: {byte2ascii(payload)}")

            # perform USB transfer
            self.write(TBP.CMD_AXIOM_COMMS, payload, self.report_id)
            rd_buffer = self.read(response_id=self.AX_TBP_RDWR_OK, ignore_response=ignore_return)

            if len(rd_buffer) == 0:
                raise AssertionError("Failed to read from device!")
            
            # validate response
            if not ignore_return:
                assert rd_buffer[0] == rx_bytes, "Invalid read header length!"

            page_buffer[offset:offset + rx_bytes] = rd_buffer[1:1 + rx_bytes]

            logger.debug("Device Response:")
            logger.debug(byte2ascii(rd_buffer))

            # prepare next read
            offset += rx_bytes
            read_address += rx_bytes

        return page_buffer

    def write_page(self, target_address, length, payload: bytearray, ignore_return=False, bl_sync=False):
        assert length == len(payload), f"length {length} and len(payload) {len(payload)} do not match."

        assert isinstance(payload, bytearray), "payload must be bytearray!"

        logger.debug(f"USB Write request at address: 0x{target_address:04x}, length: {length}")
        logger.debug(f"payload: {byte2ascii(payload)}")

        left_to_transfer = length
        read_address = target_address
        transferred = 0

        while left_to_transfer > 0:
            if left_to_transfer >= self.max_wr_pay_length:
                transfer_length = self.max_wr_pay_length
                left_to_transfer -= self.max_wr_pay_length
                addr_msb, addr_lsb = split_word(read_address)
                read_address += transfer_length  # prepare the next read
            else:
                transfer_length = left_to_transfer
                left_to_transfer = 0
                addr_msb, addr_lsb = split_word(read_address)

            logger.debug(f"Writing to address 0x{read_address:04x} with length {transfer_length}")

            length_msb, length_lsb = split_word(transfer_length)
            length_msb &= 0xFF - self.AX_COMMS_READ  # clear READ bit

            transfer_len = transfer_length + self.AX_HEADER_LEN

            transfer_payload = bytearray(transfer_len + 2)

            logger.debug("Writing to device...")
            logger.debug(f"payload: {byte2ascii(payload)}")


            if bl_sync and (self._serial_comms_mode in (0x66, 0x67)) and self.bridge_type != 'AXPB011':
                # If accumulating data in the bootloader, and I2C
                # Request to read back 8 bytes to synchronise the bootloader
                # allows us to send the next write command, without checking the busy.
                read_len = 0x8
            else:
                read_len = 0

            transfer_payload[0:6] = bytearray([transfer_len, read_len, addr_lsb, addr_msb, length_lsb, length_msb])
            transfer_payload[6:6 + transfer_length] = payload[transferred:transferred + transfer_length]

            # Write the payload to the device. Note that if using bootloader sync and in I2C mode the usb header is modified to optimise transfers.
            self.write(TBP.CMD_AXIOM_COMMS, transfer_payload, report_id=self.report_id)
            rd_buffer = self.read(self.AX_TBP_WR_OK, ignore_return)
            
            if not ignore_return:
                if len(rd_buffer) == 0:
                    raise ValueError("Expected read response!")
                if rd_buffer[0] != read_len:
                    raise ValueError(f"Invalid read response: {rd_buffer[0]}")

            if bl_sync and (self._serial_comms_mode == 0x01):
                # If accumulating data in the bootloader, and SPI
                # Request to read back 44 bytes, this synchronises the bootloader
                # allows us to send the next write command, without checking the busy.
                self.read_page(0x0100, 44)

            transferred += transfer_length

    def read_device(self):
        return self._device.read(self.hid_payload_size)
    
    def write_device(self, buffer):
        # See the following:
        # https://github.com/sergiomsilva/alpr-unconstrained/issues/73
        # For the reason of having to use the "bytes" function
        self._device.write(bytes(buffer[0:self.hid_payload_size]))


    def set_proxy_mode(self, u34_address, max_report_len):
        logger.debug("Setting USB bridge into Proxy Mode")
        logger.debug(f"target address: {u34_address}")
        logger.debug(f"max_report_len: {max_report_len}")

        addr_lsb, addr_msb = split_word(u34_address)

        tx_bytes = 4 # hardcoded for CMD_START_PROXY read, see datasheet
        payload = bytearray([0, tx_bytes, 0x58, addr_lsb, addr_msb,  0x58, self.AX_COMMS_READ])

        # perform USB transfer
        self.write(TBP.CMD_START_PROXY, payload, report_id=self.report_id)

        if self.bridge_type == "AXPB005":
            response_id = TBP.CMD_START_PROXY
        elif self.bridge_type == "AXPB007":
            response_id = self.AX_TBP_USBID_UNSOLICITED
        else:
            response_id = TBP.CMD_START_PROXY # default

        rd_buffer = self.read(response_id)

        # TODO check which bridges do what
        assert ((rd_buffer[0] == self.AX_TBP_RDWR_OK) or  # PB-005
                (rd_buffer[0] == 0x4))  # PB-007
        
        logger.debug("Bridge is in Proxy Mode!")

    def reset_bridge(self):
        logger.debug("Reset USB bridge")
        
        self.write(TBPBridge.CMD_RESET_BRIDGE, bytearray(), report_id=self.report_id)
        # There is no response, the bridge will be soft reset and re-enumerate on the USB bus

    def close(self, u34_address, max_report_len, doreset=False):
        if self.pid == self.PRODUCT_ID[0]:
            # Only do this for tbp mode...
            self.set_proxy_mode(u34_address, max_report_len)
        else:
            if doreset:
                self.reset_bridge()
            else:
                self.write(TBP.CMD_ZERO, bytearray(), report_id=self.report_id)
                logger.debug("Null Command Sent...")

    def flush_buffer(self):
        
        for i in range(30):
            self.read(ignore_response=True, timeout_ms=10)
        
        buf = self.read(ignore_response=True)
        if len(buf) > 0:
            logger.warning("Bridge buffer is not empty!")
            return False
        else:
            logger.debug("read buffer flushed...")
            return True
        
    def toggle_nreset(self):
        """
        Toggles the nRESET line by sending the CMD_RESET_AXIOM command (0x99) to the bridge.
        After each toggle, poll the buffer for a response with a timeout.
        """
        logger.debug("Toggling nRESET (CMD_RESET_AXIOM) with polling")
        self.write(TBP.CMD_RESET_AXIOM, bytearray())
        start_time = time.time()
        while time.time() - start_time < 1.0:
            if len(self.read(TBP.CMD_RESET_AXIOM, ignore_response=True)):
                logger.debug(f"Detected CMD_RESET_AXIOM response")
                break
            else: # No response, continue to next toggle
                time.sleep(0.05)
                continue
    
    def get_device_mode(self):
        """
        Sends a command to the USB device to determine its current mode.
        Returns the device mode as an integer or raises an exception if the command fails.
        """
        # Mapping of device modes to meaningful names
        device_mode_map = {
            0x81: "Error",
            0x01: "SPI",
            0x66: "I2C_66",
            0x67: "I2C_67"
        }

        try:
            self.write(TBPBridge.CMD_FIND_I2C_ADDRESS, bytearray(), report_id=self.report_id)

            usb_response = self.read(TBPBridge.CMD_FIND_I2C_ADDRESS)
            if len(usb_response) < 1:
                raise RuntimeError("No response or invalid response from device.")

            # Extract the device mode from the response
            device_mode_value = usb_response[0]

            # Map the device mode to a meaningful name, or return "Unknown" if not found
            device_mode = device_mode_map.get(device_mode_value, f"Unknown (0x{device_mode_value:02X})")
            self._serial_comms_mode = device_mode_value
            logger.info(f"Device mode: {device_mode} (0x{device_mode_value:02X})")
            return device_mode

        except Exception as e:
            logger.error(f"Failed to get device mode: {e}")
            raise