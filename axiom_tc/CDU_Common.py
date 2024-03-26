# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from time import sleep


class CDU_Common:
    CDU_CMD_FETCH = 0x0001
    CDU_CMD_STORE = 0x0002
    CDU_CMD_COMMIT = 0x0003
    CDU_CMD_QUERY = 0x0004

    CDU_XFER_SIZE = 48
    CDU_ERROR_MASK = 0x8000

    def __init__(self, axiom):
        self.__axiom = axiom

    def read(self, usage):
        length = self.__cdu_query(usage)

        return self.__cdu_fetch(usage, length)

    def write(self, usage, buffer):
        self.__cdu_store(usage, buffer)
        self.__cdu_commit(usage)

    def __cdu_query(self, usage):
        cdu_buffer = [0x00] * self.__axiom.get_usage_length(usage)

        command = CDU_Common.CDU_CMD_QUERY

        # Set the command into the buffer
        cdu_buffer[0] = (command & 0x00FF)
        cdu_buffer[1] = (command & 0xFF00) >> 8

        self.__axiom.write_usage(usage, cdu_buffer)

        while True:
            cdu_buffer = self.__axiom.read_usage(usage)
            status = cdu_buffer[0] | (cdu_buffer[1] << 8)

            # Check to see if the CDU command completed successfully.
            if status == 0:
                # Query completed OK
                param0 = cdu_buffer[2] | (cdu_buffer[3] << 8)
                param1 = cdu_buffer[4] | (cdu_buffer[5] << 8)
                param2 = cdu_buffer[6] | (cdu_buffer[7] << 8)

                # Length in bytes is param0 * param1, param 2 is not used
                # Unfortunately, u93 is still a special case - this should be
                # addressed in the future
                if usage != 0x93:
                    cdu_usage_length = param0 * param1
                else:
                    cdu_usage_length = param1 * param2
                break

        return cdu_usage_length

    def __cdu_fetch(self, usage, length):
        cdu_buffer = [0x00] * self.__axiom.get_usage_length(usage)
        result_buffer = []

        command = CDU_Common.CDU_CMD_FETCH
        offset = 0

        while offset < length:
            # Set the command in the buffer
            cdu_buffer[0] = (command & 0x00FF)
            cdu_buffer[1] = (command & 0xFF00) >> 8

            # Set the offset into the buffer
            cdu_buffer[4] = (offset & 0x00FF)
            cdu_buffer[5] = (offset & 0xFF00) >> 8

            # Send the command to aXiom to process
            self.__axiom.write_usage(usage, cdu_buffer)

            while True:
                cdu_buffer = self.__axiom.read_usage(usage)
                status = cdu_buffer[0] | (cdu_buffer[1] << 8)

                if status == 0:
                    data = cdu_buffer[8:]

                    if (offset + CDU_Common.CDU_XFER_SIZE) < length:
                        result_buffer += data
                    else:
                        result_buffer += data[:(length - offset)]

                    break
                elif (status & CDU_Common.CDU_ERROR_MASK) != 0:
                    print("ERROR: CDU Fetch Failure! Status: " + hex(status))
                else:
                    # aXiom is still processing the request
                    pass

            # Update the offset
            offset += CDU_Common.CDU_XFER_SIZE

        # Return the CDU's raw data
        return result_buffer

    def __cdu_store(self, usage, buffer):
        cdu_buffer = [0x00] * self.__axiom.get_usage_length(usage)

        command = CDU_Common.CDU_CMD_STORE
        offset = 0

        while offset < len(buffer):
            # Set the command in the buffer
            cdu_buffer[0] = (command & 0x00FF)
            cdu_buffer[1] = (command & 0xFF00) >> 8

            # Set the offset into the buffer
            cdu_buffer[4] = (offset & 0x00FF)
            cdu_buffer[5] = (offset & 0xFF00) >> 8

            # Add the chunk to the buffer. If the chunk to write is less than
            # CDU_XFER_SIZE bytes, pad it out with 0s to CDU_XFER_SIZE bytes
            if (offset + CDU_Common.CDU_XFER_SIZE) < len(buffer):
                cdu_buffer[8:] = buffer[offset:offset + CDU_Common.CDU_XFER_SIZE]
            else:
                cdu_buffer[8:] = buffer[offset:]
                padding_length = CDU_Common.CDU_XFER_SIZE - len(cdu_buffer[8:])
                padding = [0x00] * padding_length
                cdu_buffer += padding

            # Send the command to aXiom to process
            self.__axiom.write_usage(usage, cdu_buffer)

            while True:
                cdu_buffer = self.__axiom.read_usage(usage)
                status = cdu_buffer[0] | (cdu_buffer[1] << 8)

                if status == 0:
                    # Data was successfully transferred
                    break
                elif (status & CDU_Common.CDU_ERROR_MASK) != 0:
                    print("ERROR: CDU Store Failure! Status: " + hex(status))
                else:
                    # aXiom is still processing the request
                    pass

            offset += CDU_Common.CDU_XFER_SIZE

    def __cdu_commit(self, usage):
        cdu_buffer = [0x00] * self.__axiom.get_usage_length(usage)
        command = CDU_Common.CDU_CMD_COMMIT  # COMMIT to NVM

        # Set the command in the buffer and set up the magic values
        cdu_buffer[0] = (command & 0x00FF)
        cdu_buffer[1] = (command & 0xFF00) >> 8
        cdu_buffer[2] = 0x0C
        cdu_buffer[3] = 0xB1
        cdu_buffer[4] = 0xDE
        cdu_buffer[5] = 0xC0

        # Send the command to aXiom to process
        self.__axiom.write_usage(usage, cdu_buffer)

        # Long sleep to allow for enough time to write the data to flash
        sleep(0.5)

        while True:
            cdu_buffer = self.__axiom.read_usage(usage)

            status = cdu_buffer[0] | (cdu_buffer[1] << 8)
            if status == 0:
                # Data was successfully transferred
                break
            elif (status & CDU_Common.CDU_ERROR_MASK) != 0:
                print("ERROR: CDU Commit Failure! Status: " + hex(status))
            else:
                # aXiom is still processing the request
                pass
