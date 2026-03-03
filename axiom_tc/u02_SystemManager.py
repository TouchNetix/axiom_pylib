# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

from time import sleep
import logging
import time
from enum import IntEnum

from axiom_usages.axiom_usages.usages import u02

logger = logging.getLogger(__name__)

class RESPONSE(IntEnum):
    SUCCESS = 0
    BAD_COMMAND_CODE = 0x8000
    BAD_PARAMETERS_CODE = 0x8001
    RESOURCE_UNAVAILABLE_CODE = 0x8003
    WRITE_IN_PROGRESS = 0x7FFF 

class u02_SystemManager(u02):
    USAGE_ID = 0x02

    CMD_HARD_RESET = 1
    CMD_SOFT_RESET = 2
    CMD_REBASELINE = 3
    CMD_STOP = 5
    CMD_START = 6
    CMD_SAVE_CFG_TO_NVM = 7
    CMD_HANDSHAKE_NVM = 8
    CMD_COMPUTE_CRCS = 9
    CMD_FILL_CONFIG = 10
    CMD_ENTER_BOOTLOADER = 11
    CMD_START_SELF_TESTS = 12

    def __init__(self, comms, usage_address, usage_length):
        self._comms = comms
        self._usage_address = usage_address
        self._usage_length = usage_length

        self._raw = bytearray(self._usage_length)

    def read(self, ignore_return=False):
        self._raw = self._comms.read_page(self._usage_address, self._usage_length, ignore_return)
    
    def write(self, skip_verify=False, timeout=0.01):
        self._comms.write_page(self._usage_address, self._usage_length, self._raw)
        
        if not skip_verify:
            self.wait_for_idle(timeout)
                
        self.clear_flds()

    def wait_for_idle(self, timeout):
        '''
        Internal helper to poll the u02 System Manager to ensure the device is ready.
        '''
        COMMAND_TIMEOUT_LOOP_SLEEP_MS = 0.1 # matching touchhub2

        start_time = time.time()

        verified = False
        
        while True:
            try:
                time.sleep(COMMAND_TIMEOUT_LOOP_SLEEP_MS) 

                self.read(ignore_return=True)
                if self.fld_command == RESPONSE.SUCCESS:
                    verified = True
                    break
            except Exception as e:
                # Log the error if needed, or just pass to retry
                logging.debug(f"Read attempt failed: {e}")

            # Exit if we've exceeded the timeout
            if (time.time() - start_time) >= timeout:
                break
                

        if not verified:
            raise AssertionError(f"u02 command failed! Verification timeout reached. last received response: {self.fld_command}")
        
    def print(self):
        self._print_registers()

    def rebaseline(self):
        self.send_command(self.CMD_REBASELINE)

    def save_config_to_nvm(self): # Save config to NVM
        self.fld_command = self.CMD_SAVE_CFG_TO_NVM
        self.fld_parameters_0[0] = 0x0000
        self.fld_parameters_0[1] = 0xB10C
        self.fld_parameters_0[2] = 0xC0DE
        self.write(skip_verify=True)

    def fill_config(self):
        # Fill the config area with zeros
        self.fld_parameters_0[0] = 0x5555
        self.fld_parameters_0[1] = 0xAAAA
        self.fld_parameters_0[2] = 0xA55A
        self.write(timeout=0.1)

    def compute_crcs(self):
        self.fld_command = self.CMD_COMPUTE_CRCS
        self.write(timeout=0.5) # CRC computation can take ~100ms

    def handshake_nvm(self):
        self.fld_command = self.CMD_HANDSHAKE_NVM
        self.write()
        time.sleep(0.1) # Required if another u02 command happens after this one

    def start_ae(self):
        self.send_command(self.CMD_START)
        time.sleep(0.1) # wait for AE to start

    def stop_ae(self):
        self.send_command(self.CMD_STOP)
        time.sleep(0.1) # wait for AE to stop

    def soft_reset(self):
        self.fld_command = self.CMD_SOFT_RESET
        self.write(skip_verify=True)
        sleep(0.1)
        
    def trigger_self_tests(self):
        self.send_command(self.CMD_START_SELF_TESTS)
    
    def enter_bootloader(self):
        # To enter the bootloader, a sequence of writes are
        # required to ensure it is intentional to go into
        # the bootloader.
        self.fld_command = self.CMD_ENTER_BOOTLOADER
        self.fld_parameters_0[0] = 0x5555
        self.write()
        sleep(0.001)
        self.fld_command = self.CMD_ENTER_BOOTLOADER
        self.fld_parameters_0[0] = 0xAAAA
        self.write()
        sleep(0.001)
        self.fld_command = self.CMD_ENTER_BOOTLOADER
        self.fld_parameters_0[0] = 0xA55A
        self.write(skip_verify=True) # axiom should be in bootloader now
        sleep(0.5)

    def send_command(self, command):
        self.fld_command = command
        self.write()

    def _print_registers(self):
        logger.info("u02 System Manager")
        logger.info(f"  Command       : {self.fld_command:04X}")
        for i, param in enumerate(self.fld_parameters_0):
            logger.info(f"  Parameters[{i}] : {param:04X}")

