################################################################################
#                                    NOTICE
#
# Copyright (c) 2010 - 2023 TouchNetix Limited
# ALL RIGHTS RESERVED.
#
# The source  code contained  or described herein  and all documents  related to
# the source code ("Material") are owned by TouchNetix Limited ("TouchNetix") or
# its suppliers  or licensors. Title to the Material  remains with TouchNetix or
# its   suppliers  and  licensors. The  Material  contains  trade  secrets   and
# proprietary  and confidential information  of TouchNetix or its  suppliers and
# licensors.  The  Material  is  protected  by  worldwide  copyright  and  trade
# secret  laws and  treaty  provisions.  No part  of the Material  may be  used,
# copied,  reproduced,  modified,   published,  uploaded,  posted,  transmitted,
# distributed or disclosed in any way without TouchNetix's prior express written
# permission.
#
# No  license under any  patent, copyright,  trade secret or other  intellectual
# property  right is granted to or conferred upon you by disclosure or  delivery
# of  the Materials, either  expressly, by implication, inducement, estoppel  or
# otherwise.  Any  license  under  such  intellectual  property rights  must  be
# expressly approved by TouchNetix in writing.
#
################################################################################

from time import sleep

from .CDU_Common import *
from .u02_SystemManager import *

class Usage_Table_Entry:
    def __init__(self, id, start_page, num_pages, length, max_offset, offset_type, usage_rev):
        self.id          = id
        self.start_page  = start_page
        self.num_pages   = num_pages
        self.length      = length
        self.is_report   = ((num_pages == 0) and 1 or 0)
        self.max_offset  = max_offset
        self.offset_type = offset_type
        self.usage_rev   = usage_rev

    def __str__(self):
        txt = "Id: 0x{id:02x}\t Start Page: 0x{start:02x}\t Pages: {pages:3d}\t Is Report: {report:b}\t Usage Rev: {rev:2d}"
        return txt.format(id=self.id, start=self.start_page, pages=self.num_pages, report=self.is_report, rev=self.usage_rev)

class axiom:
    TIMEOUT_MS                  = 5000 # timeout before giving up in comms
    PAGE_SIZE                   =  256

    # TODO: clean the following comment when updating docs.
    # NOTE: Current documentation out of date, target addr. is not 0x0104
    BLP_FIFO_ADDRESS            = 0x0102
    BLP_REG_COMMAND             = 0x0100
    BLP_REG_STATUS              = 0x0100

    # Usages to skip over, these are read only usages. If the config file
    # includes any of these usages, it is for informational purposes only
    ignore_usage_list = [0x31, # Device Information
                         0x32, # Device Capabilities
                         0x33, # CRC Data
                         0x36, # Factory calibration data
                         0x82] # AE Controls

    # Command driven usages. They can contain an large amount of data which is
    # in efficient for aXiom to store in RAM. These usages need to be handled
    # slightly differently from normal usages.
    cdu_usage_list    = [0x05, # Comments
                         0x22, # Sequence Data
                         0x43, # Haptic Hotspots
                         0x93, # AE Profile
                         0x94] # Delta scale map

    def __init__(self, comms, read_usage_table=True, verbose=False):
        self.__comms = comms
        self.__usage_table = {}
        self.__usage_table_populated = False
        self.__verbose = verbose
        self.__max_report_len = 0
        # Pass the axiom object into comms for access to axiom data and methods
        comms.comms_init(self)

        if read_usage_table == True:
            self.build_usage_table()

        # Create a u02 object for system manager commands
        self.u02 = u02_SystemManager(self)

    def read_usage(self, usage):
        usage_content = []

        for pg in range(0, self.__usage_table[usage].num_pages):
            read_length = self.PAGE_SIZE

            # Calculate the remaining data to read for the last page
            if pg == (self.__usage_table[usage].num_pages - 1):
                read_length = self.__usage_table[usage].length - (self.PAGE_SIZE * pg)

            target_address = self.convert_usage_to_target_address(usage, pg)

            if self.__verbose: print("AX Reading Target Address: 0x%x, for usage 0x%x, length %d" % (target_address, usage, read_length))
            usage_content += self.__comms.read_page(target_address, read_length)

        return usage_content


    def write_usage(self, usage, buffer):
        buffer_offset = 0

        for pg in range(0, self.__usage_table[usage].num_pages):
            write_length = self.PAGE_SIZE

            # Calculate the remaining data to read for the last page
            if pg == (self.__usage_table[usage].num_pages - 1):
                write_length = self.__usage_table[usage].length - (self.PAGE_SIZE * pg)

            buffer_offset_end = buffer_offset + write_length
            target_address = self.convert_usage_to_target_address(usage, pg)
            if self.__verbose: print("AX Writing Target Address: 0x%x" % target_address)
            self.__comms.write_page(target_address, write_length, buffer[buffer_offset:buffer_offset_end])

            self.u02.check_usage_write_progress(usage)

            buffer_offset += self.PAGE_SIZE

    def build_usage_table(self):
            # Start Usage table build
            target_address = self.convert_usage_to_target_address(0x31, 0)
            u31_page0 = self.__comms.read_page(target_address, 12)
            num_usages = u31_page0[10]

            # Veryify the device is not in bootloader mode
            in_bootloader = u31_page0[1] & 0x80
            if in_bootloader != 0:
                print("Cannot build usage table, aXiom is in bootloader mode")
                self.__usage_table_populated = False
                return False

            target_address = self.convert_usage_to_target_address(0x31, 1)
            usage_buffer = self.__comms.read_page(target_address, (num_usages * 6))

            for usage in range(0, num_usages):
                offset      = usage * 6
                id          = usage_buffer[offset + 0]
                start_page  = usage_buffer[offset + 1]
                num_pages   = usage_buffer[offset + 2]
                max_offset  = usage_buffer[offset + 3] & 0x7F
                offset_type = usage_buffer[offset + 3] & 0x80
                usage_rev   = usage_buffer[offset + 4]

                # Calculate the usage length, taking into account reports and usages
                # that span multiple pages
                if num_pages == 0:
                    length = ((usage_buffer[offset + 3] & 0x7F) + 1) * 2
                else:
                    if id != 0x31:
                        length = ((num_pages - 1) * self.PAGE_SIZE) + (((usage_buffer[offset + 3] & 0x7F) + 1) * 2)
                    else:
                        length = self.PAGE_SIZE + (num_usages * 6)

                self.__usage_table[id] = Usage_Table_Entry(id, start_page, num_pages, length, max_offset, offset_type, usage_rev)

                if ((self.__usage_table[id].is_report) and (length > self.__max_report_len)):
                    self.__max_report_len = length

            self.__usage_table_populated = True
            return True


    def convert_usage_to_target_address(self, usage, page):
        target_address = 0
        if(self.__usage_table_populated == False and usage == 0x31):
            target_address = 0x0000 + (page << 8)
        else:
            target_address = (self.__usage_table[usage].start_page << 8) + (page << 8)
        return target_address
    
    def get_usage_revision(self, usage):
        revision = 0
        if self.__usage_table_populated == False:
            revision = 0
        else:
            revision = self.__usage_table[usage].usage_rev
        return revision

    def get_usage_length(self, usage):
        if self.__usage_table_populated == True:
            return self.__usage_table[usage].length
        else:
            return 0

    def get_max_report_len(self):
        if self.__usage_table_populated == True:
            return self.__max_report_len
        else:
            return 0

    def print_usage_table(self):
        if self.__usage_table_populated == True:
            print("Usage Table: ")
            for u in self.__usage_table:
                print(self.__usage_table[u])
        else:
            print("Usage table not yet initialised")

    def config_write_usage_to_device(self, usage, buffer):
        if usage in self.ignore_usage_list: # These are informational usages or read only
            pass
        elif usage in self.cdu_usage_list: # Command driven usages need to be handled seperately
            cdu = CDU_Common(self)
            cdu.write(usage, buffer)
            cdu_content = cdu.read(usage)

            if buffer != cdu_content:
                print("ERROR: Failed to write CDU contents. u%02X" % usage)
        else:
            self.write_usage(usage, buffer)
            usage_buffer = self.read_usage(usage)

            if buffer != usage_buffer:
                print("ERROR: Failed to write config to usage 0x%x" % (usage))
                print("Expected Length: %d and Actual Length: %d" % (len(buffer),len(usage_buffer)))
                print("Expecting: " + str(buffer))
                print("Read from Device: " + str(usage_buffer))


    def enter_bootloader_mode(self):
        attempts      = 5
        u31_ta        = self.convert_usage_to_target_address(0x31, 0)
        u31_page0     = self.__comms.read_page(u31_ta, 12)
        in_bootloader = u31_page0[1] & 0x80

        # If the chip is already in bootloader mode, no need to continue
        if in_bootloader != 0:
            return True

        # Depending on the sequence, the usage table may not be populated at
        # this moment. The device is not in bootloader mode, so it should be
        # safe to build the usage table. The usage table is required to send the
        # appropiate system manager commands to aXiom to get it into bootloader
        # mode
        if self.__usage_table_populated == False:
            self.build_usage_table()

        # Attempt to enter bootloader mode
        while (in_bootloader == 0) and (attempts > 0):
            # Entering bootloader mode is "involved" to ensure it is a deliberate
            # request. Three "enter bootloader" commands are required, the number
            # on the end is the sequence number, that will send the appropiate
            # "magic" number to aXiom. If all is well, aXiom will be in the
            # bootloader a few moments after the last command.
            self.u02.send_command(self.u02.CMD_ENTER_BOOTLOADER)

            # Read for the bootloader flag
            u31_page0     = self.__comms.read_page(u31_ta, 12)
            in_bootloader = u31_page0[1] & 0x80

            if in_bootloader != 0:
                # Bootloader flag is set, no need to continue.
                break

            attempts -= 1

        return True if (in_bootloader != 0) else False


    def print_device_info(self):
        buffer = self.get_u31_device_info()

        device_id            = ((buffer[1] & 0x7f) << 8) + buffer[0]
        device_channel_count = device_id & 0x3FF
        device_variant       = (device_id & 0x7C00) >> 10

        fw_ver_major = int(buffer[3])
        fw_ver_minor = int(buffer[2])
        fw_ver_rc    = (buffer[11] & 0xf0) >> 4

        bl_ver_major = int(buffer[7])
        bl_ver_minor = int(buffer[6])

        silicon_id   = (int(buffer[9]) << 8) + int(buffer[8])
        silicon_rev  = chr(0x41 + (buffer[11] & 0xf))

        print("  Device ID   : AX%u%c " % (device_channel_count, chr(0x41 + device_variant)))
        print("  FW Revision : %d.%02d (RC%d)" % ( fw_ver_major, fw_ver_minor, fw_ver_rc))
        print("  BL Revision : %d.%02d" % (bl_ver_major, bl_ver_minor))
        print("  Silicon     : 0x%04X (Rev %c)" % (silicon_id, silicon_rev))
        print("")

    def get_u31_device_info(self):
        return self.__comms.read_page(0x0, 12)

    def bootloader_get_busy_status(self):
        status = self.__comms.read_page(self.BLP_REG_STATUS, 4)
        # Busy bit is bit 0 of byte 2
        return (status[2] & 0x01) != 0

    def bootloader_reset_axiom(self):
        self.__comms.write_page(self.BLP_REG_COMMAND, 2, [0x02, 0x00])

    def bootloader_write_chunk(self, header, payload):
        busy_time = 0
        # Ensure aXiom is available to process our request
        current_timeout = 0
        while self.bootloader_get_busy_status() == True:
            # aXiom is busy, wait 1ms before trying again
            if current_timeout < self.TIMEOUT_MS:
                current_timeout = current_timeout + 1
            else:
                print("ERROR: aXiom does not seem to be responding...")
                raise TimeoutError

            sleep(0.001)

        # Write the header data from the file
        self.__comms.write_page(self.BLP_FIFO_ADDRESS, len(header), header)
        if self.__verbose:
            print("wrote header %d bytes" % len(header))

        # Ensure aXiom is available to process our request
        current_timeout = 0
        while self.bootloader_get_busy_status() == True:
            # aXiom is busy, wait 1ms before trying again
            if current_timeout < self.TIMEOUT_MS:
                current_timeout = current_timeout + 1
            else:
                print("ERROR: aXiom does not seem to be responding...")
                raise TimeoutError
            busy_time += 1
            sleep(0.001)

        # Break the chunk into smaller, more managable payloads
        offset = 0
        length = len(payload)

        # The following slicing depends on the type of communication link.
        # here we probe the comms class to see if we have any USB specific
        # constants declared. If this is not the case then we assume chunk
        # size compatible with i2c/SPI.
        try:
            if (self.__comms.wMaxPacketSize > self.PAGE_SIZE):
                chunk_size = (self.PAGE_SIZE-1) - self.__comms.AX_HEADER_LEN
            else:
                chunk_size = (self.__comms.wMaxPacketSize-1) \
                         - self.__comms.AX_TBP_I2C_DEV_HEAD_LEN \
                         - self.__comms.AX_HEADER_LEN
        except:
            chunk_size = self.PAGE_SIZE-1

        while offset < length:
            length_to_write = 0

            # Calculate how much data to transfer, up to the max transfer size
            if (offset + chunk_size) < length:
                length_to_write = chunk_size
            else:
                length_to_write = length - offset

            # Extract the data to be transferred
            payload_chunk = payload[offset:(offset + length_to_write)]

            # Send the data to aXiom
            self.__comms.write_page(self.BLP_FIFO_ADDRESS, length_to_write, payload_chunk)
            if self.__verbose:
                print("wrote %d bytes" % length_to_write)

            # Ensure aXiom is available to process our request
            current_timeout = 0
            while self.bootloader_get_busy_status() == True:
                # aXiom is busy, wait 1ms before trying again
                if current_timeout < self.TIMEOUT_MS:
                    current_timeout = current_timeout + 1
                else:
                    print("ERROR: aXiom does not seem to be responding...")
                    raise TimeoutError
                busy_time += 1
                sleep(0.001)
            offset += length_to_write
        if self.__verbose:
            print("busy_time was %d" % busy_time)

    def close(self):
        self.__comms.close()
