from time import sleep

from .CDU_Common import CDU_Common
from .u02_SystemManager import u02_SystemManager
from .u31_DeviceInformation import u31_DeviceInformation

class axiom:
    TIMEOUT_MS                  = 5000 # timeout before giving up in comms

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
                         0x77, # Dial on Display
                         0x93, # AE Profile
                         0x94] # Delta scale map

    def __init__(self, comms, read_usage_table=True):
        self._comms   = comms

        # Pass the axiom object into comms for access to axiom data and methods
        comms.comms_init(self)

        # Objects to usages that are key to most axiom operations
        self.u31 = u31_DeviceInformation(self, read_usage_table)
        self.u02 = u02_SystemManager(self)

    def read_usage(self, usage):
        usage_content = []

        for pg in range(0, self.u31._usage_table[usage].num_pages):
            read_length = self.u31.PAGE_SIZE
            # Calculate the remaining data to read for the last page
            if pg == (self.u31._usage_table[usage].num_pages - 1):
                read_length = self.u31._usage_table[usage].length - (self.u31.PAGE_SIZE * pg)

            target_address = self.u31.convert_usage_to_target_address(usage, pg)
            usage_content += self._comms.read_page(target_address, read_length)

        return usage_content


    def write_usage(self, usage, buffer):
        buffer_offset = 0

        for pg in range(0, self.u31._usage_table[usage].num_pages):
            write_length = self.u31.PAGE_SIZE

            # Calculate the remaining data to read for the last page
            if pg == (self.u31._usage_table[usage].num_pages - 1):
                write_length = self.get_usage_length(usage) - (self.u31.PAGE_SIZE * pg)

            buffer_offset_end = buffer_offset + write_length
            target_address = self.u31.convert_usage_to_target_address(usage, pg)

            self._comms.write_page(target_address, write_length, buffer[buffer_offset:buffer_offset_end])
            self.u02.check_usage_write_progress(usage)

            buffer_offset += self.u31.PAGE_SIZE
    
    def get_usage_revision(self, usage):
        revision = 0
        if self.u31._usage_table_populated == False:
            revision = 0
        else:
            revision = self.u31._usage_table[usage].usage_rev
        return revision

    def get_usage_length(self, usage):
        if self.u31._usage_table_populated == True:
            return self.u31._usage_table[usage].length
        else:
            return 0

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
        u31_ta        = self.u31.convert_usage_to_target_address(0x31, 0)
        u31_page0     = self._comms.read_page(u31_ta, 12)
        in_bootloader = u31_page0[1] & 0x80

        # If the chip is already in bootloader mode, no need to continue
        if in_bootloader != 0:
            return True

        # Depending on the sequence, the usage table may not be populated at
        # this moment. The device is not in bootloader mode, so it should be
        # safe to build the usage table. The usage table is required to send the
        # appropiate system manager commands to aXiom to get it into bootloader
        # mode
        if self.u31._usage_table_populated == False:
            self.u31.build_usage_table()

        # Attempt to enter bootloader mode
        while (in_bootloader == 0) and (attempts > 0):
            # Entering bootloader mode is "involved" to ensure it is a deliberate
            # request. Three "enter bootloader" commands are required, the number
            # on the end is the sequence number, that will send the appropiate
            # "magic" number to aXiom. If all is well, aXiom will be in the
            # bootloader a few moments after the last command.
            self.u02.send_command(self.u02.CMD_ENTER_BOOTLOADER)

            # Read for the bootloader flag
            u31_page0     = self._comms.read_page(u31_ta, 12)
            in_bootloader = u31_page0[1] & 0x80

            if in_bootloader != 0:
                # Bootloader flag is set, no need to continue.
                break

            attempts -= 1

        return True if (in_bootloader != 0) else False

    def bootloader_get_busy_status(self):
        status = self._comms.read_page(self.BLP_REG_STATUS, 4)
        # Busy bit is bit 0 of byte 2
        return (status[2] & 0x01) != 0

    def bootloader_reset_axiom(self):
        self._comms.write_page(self.BLP_REG_COMMAND, 2, [0x02, 0x00])

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
        self._comms.write_page(self.BLP_FIFO_ADDRESS, len(header), header)

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
            if (self._comms.wMaxPacketSize > self.u31.PAGE_SIZE):
                chunk_size = (self.u31.PAGE_SIZE-1) - self._comms.AX_HEADER_LEN
            else:
                chunk_size = (self._comms.wMaxPacketSize-1) \
                        - self._comms.AX_TBP_I2C_DEV_HEAD_LEN \
                        - self._comms.AX_HEADER_LEN
        except:
            chunk_size = self.u31.PAGE_SIZE-1

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
            self._comms.write_page(self.BLP_FIFO_ADDRESS, length_to_write, payload_chunk)

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

    def close(self):
        self._comms.close()
