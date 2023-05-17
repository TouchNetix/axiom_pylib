################################################################################
#                                    NOTICE
#
# Copyright (c) 2010 - 2020 TouchNetix Limited
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

class CDU_Common:
    CDU_CMD_FETCH  = 0x0001
    CDU_CMD_STORE  = 0x0002
    CDU_CMD_COMMIT = 0x0003
    CDU_CMD_QUERY  = 0x0004

    CDU_XFER_SIZE  =     48
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
        cdu_buffer       = [0x00] * self.__axiom.get_usage_length(usage)
        cdu_usage_length = 0

        command = CDU_Common.CDU_CMD_QUERY

        # Set the command into the buffer
        cdu_buffer[0] = ( command & 0x00FF )
        cdu_buffer[1] = ( command & 0xFF00 ) >> 8

        self.__axiom.write_usage(usage, cdu_buffer)

        while True:
            cdu_buffer = self.__axiom.read_usage(usage)
            status     = cdu_buffer[0] | (cdu_buffer[1] << 8)

            # Check to see if the CDU command completed successfully.
            if status == 0:
                # Query completed OK
                param0 = cdu_buffer[2] | (cdu_buffer[3] << 8)
                param1 = cdu_buffer[4] | (cdu_buffer[5] << 8)
                param2 = cdu_buffer[6] | (cdu_buffer[7] << 8)

                # Length in bytes is param0 * param1, param 2 is not used
                # Unfortunatly, u93 is still a special case - this should be
                # addressed in the future
                if usage != 0x93:
                    cdu_usage_length = param0 * param1
                else:
                    cdu_usage_length = param1 * param2
                break

        return cdu_usage_length

    def __cdu_fetch(self, usage, length):
        cdu_buffer    = [0x00] * self.__axiom.get_usage_length(usage)
        result_buffer = []

        command = CDU_Common.CDU_CMD_FETCH
        offset  = 0

        while offset < length:
            # Set the command in the buffer
            cdu_buffer[0] = ( command & 0x00FF )
            cdu_buffer[1] = ( command & 0xFF00 ) >> 8

            # Set the offset into the buffer
            cdu_buffer[4] = ( offset & 0x00FF )
            cdu_buffer[5] = ( offset & 0xFF00 ) >> 8

            # Send the command to aXiom to process
            self.__axiom.write_usage(usage, cdu_buffer)

            while True:
                cdu_buffer = self.__axiom.read_usage(usage)
                status     = cdu_buffer[0] | (cdu_buffer[1] << 8)

                if status == 0:
                    data = cdu_buffer[8:]

                    if (offset + CDU_Common.CDU_XFER_SIZE) < length:
                        result_buffer += data
                    else:
                        result_buffer += data[:(length-offset)]

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
        offset  = 0

        while offset < len(buffer):
            # Set the command in the buffer
            cdu_buffer[0] = ( command & 0x00FF )
            cdu_buffer[1] = ( command & 0xFF00 ) >> 8

            # Set the offset into the buffer
            cdu_buffer[4] = ( offset & 0x00FF )
            cdu_buffer[5] = ( offset & 0xFF00 ) >> 8

            # Add the chunk to the buffer. If the chunk to write is less than
            # CDU_XFER_SIZE bytes, pad it out with 0s to CDU_XFER_SIZE bytes
            if (offset + CDU_Common.CDU_XFER_SIZE) < len(buffer):
                cdu_buffer[8:] = buffer[offset:offset+CDU_Common.CDU_XFER_SIZE]
            else:
                cdu_buffer[8:] = buffer[offset:]
                padding_length = CDU_Common.CDU_XFER_SIZE - len(cdu_buffer[8:])
                padding = [0x00] * (padding_length)
                cdu_buffer += padding

            # Send the command to aXiom to process
            self.__axiom.write_usage(usage, cdu_buffer)

            while True:
                cdu_buffer = self.__axiom.read_usage(usage)
                status     = cdu_buffer[0] | (cdu_buffer[1] << 8)

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
        command    = CDU_Common.CDU_CMD_COMMIT # COMMIT to NVM

        # Set the command in the buffer and setup the magic values
        cdu_buffer[0] = ( command & 0x00FF )
        cdu_buffer[1] = ( command & 0xFF00 ) >> 8
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
