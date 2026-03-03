# Copyright (c) 2024 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

import logging
import time 
from enum import Enum

from axiom_usages.axiom_usages.usage import Usage
from axiom_usages.axiom_usages import init_usages
from axiom_usages.axiom_usages.usages import u01, u34

from . import cdu
from .UsageManager import UsageManager
from .u02_SystemManager import u02_SystemManager
from .u31_DeviceInformation import u31_DeviceInformation
from .u33_CRCData import u33_CRCData
from .Bootloader import Bootloader, RESET_TIMEOUT
from .u06_SelfTest import u06_SelfTest
from .u07_LiveView import u07_LiveView
from .u03_SystemControls import u03_SystemControls
from .u32_DeviceCapabilities import u32_DeviceCapabilities
from .u34_ReportController import u34_ReportController
from .u48_GPIOControls import u48_GPIOControls

logger = logging.getLogger(__name__)

class axiom:
    """
    Initialize the aXiom device object and core usages.

    Sets up communication, reads the device usage table, and verifies
    usage versions. If usage imports are outdated, regenerates them and exits.

    Initializes core usages unless the device is in bootloader mode.
    """
    
    PAGE_SIZE = 256
    BLP_REG_COMMAND = 0x0100

    def __init__(self, comms, skip_exit=False, bl_ok=False):
        self._comms = comms
        self._cdu_info = {}

        comms.comms_init()

        # TODO initial check to see if axiom exists before proceeding, e.g like i2cdetect

        self.u31 = u31_DeviceInformation(self._comms)

        if self.u31.fld_mode == self.u31.MODE_Enum.BOOTLOADER_BLP_:
            
            reset_ok = self.reset_axiom()

            if not reset_ok: 
                # axiom is stuck in bootloader, continue with bl_ok if we
                # want to attempt to recover it with a firmware download
                if bl_ok: 
                    self.bl = Bootloader(self._comms)
                    return
                else:
                    raise AssertionError("Connection to aXiom failed!")
        
        
        if not self.u31.usage_table_populated:
            raise AssertionError("aXiom cannot be initialized!")
        
        # axiom should be in a valid runtime state now 
        self._u34_address = self.u31.get_usage_address(0x34)
        self._max_report_len = self.u31.max_report_len

        # check usage imports match the connected device, if not regenerate them
        usage_vers = self.u31.get_usage_vers()
        if not self._check_usage_revs(usage_vers):
            logger.info("New device connected. New imports will be generated based upon the device revisions.")
            init_usages.generate_usages_init(self.u31.get_device_info_short(), usage_vers)
            logger.info("New usage table imports have been generated. Please restart.")
            if not skip_exit:
                self.close()
                exit(0)

        # prepopulate CDU info
        for usage in self.u31.get_usages():
            if self.u31.is_cdu(usage):
                self._cdu_info[usage] = cdu.query(self._comms, self.u31.get_usage_address(usage), usage) 

        # --- init all axiom usages here ---
        self.u02 = u02_SystemManager(self._comms, 
            self.u31.get_usage_address(0x02), 
            self.u31.get_usage_entry(0x02).length)
        self.usg_mngr = UsageManager(self._comms, 
            self.u02)
        self.bl = Bootloader(self._comms, 
            self.u02, 
            self.u31)
        self.u33 = u33_CRCData(self.read_usage(0x33),
            self.u31.get_supported_usages())
        self.u32 = u32_DeviceCapabilities(self.read_usage(0x06))
        self.u06 = u06_SelfTest(self.read_usage(0x06))
        self.u07 = u07_LiveView(self.read_usage(0x07))
        self.u03 = u03_SystemControls(self.read_usage(0x03))
        self.u48 = u48_GPIOControls(self.read_usage(0x48))

    def _check_usage_revs(self, device_usage_vers):
        """
        Compare connected device's usage versions with local usage imports.
        """
        current_usage_imports = init_usages.parse_usage_versions()
        available_usages = init_usages.get_available_usages()
        
        for usage_id, rev in device_usage_vers.items():
            if usage_id in available_usages.keys():
                if usage_id not in current_usage_imports.keys():
                    return False
                elif rev != current_usage_imports[usage_id] and rev in available_usages[usage_id]:
                    return False
            
        return True

    def read_usage(self, usage):
        if not self.u31.usage_table_populated:
            raise AssertionError(f"Cannot read usage {usage:02x} aXiom is not initialized!")
        if usage not in self.u31.get_usages():
            raise LookupError(f"usage u{usage:02x} does not exist!")
        if self.u31.is_report(usage):
            raise AssertionError(f"usage u{usage:02x} is a report, reports are read through u34.")
            
        usage_bytes = self.usg_mngr.read(self.u31.get_usage_address(usage), self.u31.get_usage_entry(usage).length)

        # populate the usage class bytes if available
        usage_attr_name = f"u{usage:02x}"
        if hasattr(self, usage_attr_name):
            usage_obj: Usage = getattr(self, usage_attr_name)
            
            # the usage length in u31 and the one in the TCP revision may not match 
            usage_obj.set_bytes(usage_bytes[:usage_obj.USAGE_LEN])

        # Return a copy to the caller different from the internal state
        return usage_bytes.copy()
    
    def write_usage(self, usage, usage_bytes=None, save_to_nvm=True):
        if not self.u31.usage_table_populated:
            raise AssertionError(f"Cannot read usage {usage:02x} aXiom is not initialized!")
        if usage not in self.u31.get_usages():
            raise LookupError(f"usage u{usage:02x} does not exist!")

        # use the class usage bytes if available        
        if usage_bytes is None:
            usage_attr_name = f"u{usage:02x}"
            if not hasattr(self, usage_attr_name):
                raise ValueError(f"Usage {usage_attr_name} is not supported or defined in this class, usage bytes must be passed in directly.")

            usage_obj: Usage = getattr(self, usage_attr_name)

            usage_bytes = usage_obj._raw 

        if not self.u31.usage_table_populated:
            raise AssertionError(f"Cannot write usage {usage:02x} aXiom is not initialized!")

        if self.u31.is_read_only(usage):
            raise AssertionError(f"Cannot write read only usage u{usage:02x}!")

        if len(usage_bytes) > self.get_usage_length(usage):
            raise AssertionError(f"Attempting to write buffer that is longer than usage u{usage:02x}! \n" \
                                f"buffer: {len(usage_bytes)}, usage: {self.get_usage_length(usage)}")
            
        if self.u31.is_cdu(usage):
            cdu.write(self._comms, 
                        self.u31.get_usage_address(usage),  
                        usage_bytes)
            self.save_cdu_config(usage)
        else:
            self.usg_mngr.write(self.u31.get_usage_address(usage), 
                        len(usage_bytes), 
                        usage_bytes)

            if save_to_nvm:
                self.save_config()

        return 

    def save_cdu_config(self, usage):
        """
        Follow the handshake process to save a command driven usage to NVM:
        1. Commit the given CDU
        2. Wait for OPCOMPLETE u02 report
        3. Send HANDSHAKENVM to complete handshake
        The AE must be stopped in order to write a CDU.
        """
        cdu_save_timeout = 0.5

        self.clear_reports()

        cdu.commit(self._comms, self.u31.get_usage_address(usage))

        self.wait_for_u01_report(u01.REPORTTYPE_Enum.OPCOMPLETE, cdu_save_timeout)

        self.u02.handshake_nvm()

        # TODO verify CDU CRC

    def save_config(self):
        """
        Save non-CDU usages to NVM: 
        1. Send CMD_SAVE_CONFIG
        2. Wait for OPCOMPLETE u02 report for CMD_SAVE_CONFIG 
        3. Send HANDSHAKENVM to complete handshake
        The AE must be stopped in order to write a config to NVM.
        """
        cfg_save_timeout = 3.0 # Can take a while if done repeatedly

        self.clear_reports()
        
        self.read_usage(0x07)
        ae_state = self.u07.fld_aestatus_run
        if ae_state == self.u07.AESTATUS_RUN_Enum.RUNNING:
            self.u02.stop_ae() # AE must be stopped to save to NVM

        self.u02.save_config_to_nvm()

        self.wait_for_u01_report(u01.REPORTTYPE_Enum.OPCOMPLETE, cfg_save_timeout)

        self.u02.handshake_nvm()

        self.u02.compute_crcs()
        self.read_usage(0x33)
  
        # # Now check the NVM and RAM CRCs match
        if self.u33.fld_nvltlusageconfig_crc != self.u33.fld_vltusageconfig_crc:
            raise AssertionError(f"Failed to save config! NVM Usage Config CRC: 0x{self.u33.fld_nvltlusageconfig_crc:08X} RAM Usage Config CRC: 0x{self.u33.fld_vltusageconfig_crc:08X}")
        
        if ae_state == self.u07.AESTATUS_RUN_Enum.RUNNING:
            # restart required
            self.u02.start_ae()

    def get_usage_length(self, usage):
        
        if usage not in self.u31.get_usages():
            raise LookupError(f"usage u{usage:02x} does not exist!")

        if self.u31.is_cdu(usage):
            return self._cdu_info[usage]
        else:
            return self.u31.get_usage_entry(usage).length
    
    def close(self):
        if self.u31.is_in_bootloader_mode():
            self.reset_axiom()    
        
        self._comms.close(self.u31.get_usage_address(0x34), self.u31.max_report_len)

    def clear_reports(self):
        """
        Clear any reports that are already in the u34 buffer
        """        
        num_reports = 5
        for _ in range(num_reports):
            report = self._comms.read_page(self._u34_address, self._max_report_len)
            
            if u34_ReportController(report).fld_reportusage == 0:
                break
    
    def wait_for_u01_report(self, report_val, timeout):
        """
        Synchronously polls the device for a specific report.
        Returns True if the report is received, False otherwise.
        """
        if not isinstance(report_val, (Enum, int)):
            raise ValueError(f"The expected field is either an enum or int: {report_val}")

        # matching pre polling sleep with touchhub2, it would be good to 
        # do without this but otherwise there are comms failures with axiom.
        time.sleep(1)

        logger.debug(f"Polling for report: {report_val}...")

        start_time = time.time()
        while True:
            try:
                report = self._comms.read_page(self._u34_address, self._max_report_len)
                
                if report:
                    u34_ctrl = u34_ReportController(report)
                    if u34_ctrl.fld_reportusage == 0x01:
                        u01_rpt = u01(report)
                        if u01_rpt.fld_reporttype == report_val:
                            logger.debug(f"Report received: {report_val}")
                            logger.debug(f"time: {time.time() - start_time}")
                            return True
                        
                time.sleep(0.01) # A generous delay while polling
                
            except Exception as e:
                logger.debug(f"Error during poll: {e}")

            if (time.time() - start_time) >= timeout:
                break

        logger.warning(f"Timeout waiting for report: {report_val}")
        return False

    def reset_axiom(self):

        # option 1 runtime reset and wait for hello using IRQ
        # option 2 runtime reset and wait for reset timeout
        # option 3 bootloader reset and wait for hello using IRQ
        # option 4 bootloader reset and wait for reset timeout
        # if doesnt work:
        # option 5 toggle nRESET until axiom enters bootloader

        # Otherwise, stuck in bootloader and there is an axiom issue!

        # Use bl reset if in bootloader, otherwise use u02
        use_bl_reset = self.u31.is_in_bootloader_mode()

        # axiom can get stuck in bootloader mode, so try multiple resets
        attempts = 3
        while attempts > 0:

            if use_bl_reset:
                self._comms.write_page(self.BLP_REG_COMMAND, 2, bytearray([0x02, 0x00]), ignore_return = True)
            else:
                self.u02.soft_reset() 

            time.sleep(1) # wait for axiom to be ready to receive comms

            if self.u31.usage_table_populated:
                if self.wait_for_u01_report(u01.REPORTTYPE_Enum.HELLO, RESET_TIMEOUT):
                    logger.debug("Runtime detected via hello report.")
                    time.sleep(0.1)
                    break

            logger.debug("Using sleep fallback.")

            time.sleep(RESET_TIMEOUT)
            
            if not self.u31.is_in_bootloader_mode():
                logger.debug("Runtime detected.")
                break

            attempts -= 1
            logger.warning(f"Reset attempt failed, retrying...")

        if attempts == 0: # Failed to exit using standard methods, now try nRESET line if available
            runtime_ok = False
            if hasattr(self._comms, "toggle_nreset"):
                toggle_nreset_attempts = 3
                while toggle_nreset_attempts > 0:
                    self._comms.toggle_nreset()
                    time.sleep(RESET_TIMEOUT) 
                    if not self.u31.is_in_bootloader_mode():
                        logger.debug("Runtime detected.")
                        runtime_ok = True
                        break
                    toggle_nreset_attempts -= 1

            if not runtime_ok:
                logger.error("Failed to exit aXiom bootloader!")
                return False
        
        # axiom should now be out of bootloader and the usage table can be repopulated
        self.u31.read_all()

        return True