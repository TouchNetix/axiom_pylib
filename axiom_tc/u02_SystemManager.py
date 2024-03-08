# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import struct
from time import sleep


class u02_SystemManager:
    USAGE_ID = 0x02

    CMD_HARD_RESET = 1
    CMD_SOFT_RESET = 2
    CMD_REBASELINE = 3
    CMD_STOP = 5
    CMD_START = 6
    CMD_SAVE_CONFIG = 7
    CMD_COMPUTE_CRCS: int = 9
    CMD_FILL_CONFIG = 10
    CMD_ENTER_BOOTLOADER = 11
    CMD_RUN_SELF_TESTS = 12

    def __init__(self, axiom):
        self._axiom = axiom

        # Get the usage number from the axiom class
        self._usage_revision = self._axiom.get_usage_revision(self.USAGE_ID)

        # Initialise a buffer for the usage's contents to be read into and unpacked/packed
        self._usage_binary_data = [0] * self._axiom.get_usage_length(self.USAGE_ID)

        # To handle different usage revisions, there are different methods that handle
        # register initialisation (in this python class), dumping out the contents of
        # a usage and unpacking and packing the usage's variables back into binary formats.
        # Use the getattr() find find the appropriate methods that pertain the usage revision.
        self._init_registers = getattr(self, "_init_registers_uifrev{}".format(self._usage_revision), None)
        self._print_registers = getattr(self, "_print_registers_uifrev{}".format(self._usage_revision), None)
        self._unpack_registers = getattr(self, "_unpack_uifrev{}".format(self._usage_revision), None)
        self._pack_registers = getattr(self, "_pack_uifrev{}".format(self._usage_revision), None)

        # Raise an exception if an unsupported version of the usage is found.
        if (self._init_registers is None or
                self._print_registers is None or
                self._unpack_registers is None or
                self._pack_registers is None):
            raise Exception(
                "Unsupported revision of {}. Revision: {}".format(self.__class__.__name__, self._usage_revision))

        # Initialise the variables that are supported by this revision of the usage.
        # With new firmware, the usage could be up-revved and new methods will need
        # to be added
        self._init_registers()

    def read(self):
        self._usage_binary_data = self._axiom.read_usage(self.USAGE_ID)
        self._unpack()

    def write(self):
        self._pack()
        self._axiom.write_usage(self.USAGE_ID, self._usage_binary_data)

    def print(self):
        self._print_registers()

    def _unpack(self):
        self._unpack_registers()

    def _pack(self):
        self._pack_registers()

    # region u02 Specific Methods
    def send_command(self, command):
        skip_verify = False
        self.reg_command = command

        if command == self.CMD_SAVE_CONFIG:
            self.reg_parameters[0] = 0x0000
            self.reg_parameters[1] = 0xB10C
            self.reg_parameters[2] = 0xC0DE
            self.write()
            sleep(0.1)
        elif command == self.CMD_ENTER_BOOTLOADER:
            # To enter the bootloader, a sequence of writes are
            # required to ensure it is intentional to go into
            # the bootloader.
            skip_verify = True
            self.reg_command = command
            self.reg_parameters[0] = 0x5555
            self.write()
            sleep(0.001)
            self.reg_command = command
            self.reg_parameters[0] = 0xAAAA
            self.write()
            sleep(0.001)
            self.reg_command = command
            self.reg_parameters[0] = 0xA55A
            self.write()
            sleep(0.2)
        elif command == self.CMD_FILL_CONFIG:
            # Fill the config area with zeros
            self.reg_command = command
            self.reg_parameters[0] = 0x5555
            self.reg_parameters[1] = 0xAAAA
            self.reg_parameters[2] = 0xA55A
            self.write()
            sleep(0.1)
        else:
            # Don't perform u02 verify reads for reset commands
            if (command == self.CMD_HARD_RESET or
                    command == self.CMD_SOFT_RESET):
                skip_verify = True

            self.write()
            sleep(0.1)

        # Check the status of the command for up to 1 second (10ms sleeps)
        if not skip_verify:
            for _ in range(100):
                # Update the registers
                self.read()

                # Check the command value, if it is 0, then the command has
                # completed successfully. If the command register still has
                # the same value as the written command value, then the command
                # is still in progress. Any other response would indicate an error.
                if self.reg_command == command:
                    # Command is still in progress
                    sleep(0.01)
                    continue
                elif self.reg_command == 0x0000:
                    # Command completed successfully
                    return 0
                else:
                    # Command failed
                    print("ERROR: u02 System Manager command failed with error code: %04X" % self.reg_command)
                    return self.reg_command
        return 0

    def check_usage_write_progress(self, usage):
        # After a usage write, the firmware will notify the relevant usages of a
        # config update. This notification is done via u02 System Manager. This
        # is a belts and braces check which helps rate limit usage writes in any
        # instances whereby a config update takes longer to process.

        # Skip over u02, we are interested in the other usages.
        # Also skip over CDUs as they have their own mechanisms
        if (usage == self.USAGE_ID) or (usage in self._axiom.cdu_usage_list):
            return

        # Retry 1000 times over 1s.
        for _ in range(1000):
            self.read()

            if self.reg_command == 0x0000:
                # Response value of zero indicates that u02 is not currently
                # busy. We can safely return now.
                return

            # A response of 0x7FFF indicates that u02 is reporting that it is
            # still processing the last read. However, as a catch-all, attempt
            # a retry until all retries expire.
            sleep(0.001)  # sleep 1ms, give the device some time to complete

        # Should not get here - this error should be handled. Seeing this error
        # message indicates that a usage was written, aXiom then processes the
        # update and aXiom was still reporting that it was busy after 1 second
        # (10 retries with 100ms delays).
        print("ERROR: u02 In progress. u%02X - %04X" % (usage, self.reg_command))

    # endregion

    # region u02 System Manager Usage Revision 1
    def _init_registers_uifrev1(self):
        self.reg_command = 0
        self.reg_parameters = [0] * 3

    def _unpack_uifrev1(self):
        command, param0, param1, param2 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[0:8])))
        self.reg_command = command
        self.reg_parameters[0] = param0
        self.reg_parameters[1] = param1
        self.reg_parameters[2] = param2

    def _pack_uifrev1(self):
        # Convert the usage binary data into a byte array for struct pack to work
        usage_as_bytearray = bytearray(self._usage_binary_data)

        fields = [0] * 4
        fields[0] = self.reg_command
        fields[1] = self.reg_parameters[0]
        fields[2] = self.reg_parameters[1]
        fields[3] = self.reg_parameters[2]
        struct.pack_into("<4H", usage_as_bytearray, 0, *fields)

        # Convert the binary usage data into a list
        self._usage_binary_data = list(usage_as_bytearray)

    def _print_registers_uifrev1(self):
        print("u02 System Manager")
        print("  Command       : %04X" % self.reg_command)
        print("  Parameters[0] : %04X" % self.reg_parameters[0])
        print("  Parameters[1] : %04X" % self.reg_parameters[1])
        print("  Parameters[2] : %04X" % self.reg_parameters[2])

    # endregion

    # region u02 System Manager Usage Revision 2
    def _init_registers_uifrev2(self):
        self.reg_command = 0
        self.reg_parameters = [0] * 3

    def _unpack_uifrev2(self):
        command, param0, param1, param2 = struct.unpack("<4H", bytes(bytearray(self._usage_binary_data[0:8])))
        self.reg_command = command
        self.reg_parameters[0] = param0
        self.reg_parameters[1] = param1
        self.reg_parameters[2] = param2

    def _pack_uifrev2(self):
        # Convert the usage binary data into a byte array for struct pack to work
        usage_as_bytearray = bytearray(self._usage_binary_data)

        fields = [0] * 4
        fields[0] = self.reg_command
        fields[1] = self.reg_parameters[0]
        fields[2] = self.reg_parameters[1]
        fields[3] = self.reg_parameters[2]
        struct.pack_into("<4H", usage_as_bytearray, 0, *fields)

        # Convert the binary usage data into a list
        self._usage_binary_data = list(usage_as_bytearray)

    def _print_registers_uifrev2(self):
        print("u02 System Manager")
        print("  Command       : %04X" % self.reg_command)
        print("  Parameters[0] : %04X" % self.reg_parameters[0])
        print("  Parameters[1] : %04X" % self.reg_parameters[1])
        print("  Parameters[2] : %04X" % self.reg_parameters[2])
# endregion
