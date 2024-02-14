import struct

class _Usage_Table_Entry:
    USAGE_TABLE_ENTRY_SIZE = 6

    def __init__(self, id, start_page, num_pages, length, max_offset, offset_type, usage_rev):
        self.id          = id
        self.start_page  = start_page
        self.num_pages   = num_pages
        self.length      = length
        self.is_report   = True if (num_pages == 0) else False
        self.max_offset  = max_offset
        self.offset_type = offset_type
        self.usage_rev   = usage_rev

    def __str__(self):
        text = "Usage: u{0:02x}    Rev: {1:3d}    Page: 0x{2:02x}00    Num Pages: {3:3d}    Length: {4:5d}    {5:s}"
        return text.format(self.id, self.usage_rev, self.start_page, self.num_pages, self.length, "Report" if self.is_report else "")

class u31_DeviceInformation:
    USAGE_ID           = 0x31

    u31_TARGET_ADDRESS = 0x0000
    u31_PAGE_0_LEN     = 12
    PAGE_SIZE          = 256

    FW_VARIANTS = ["3D", "2D", "FORCE"]

    def __init__(self, axiom, read = True, read_usage_table=True):
        self._axiom = axiom

        # Get the usage number from the axiom class
        self._usage_revision = 1 # self._axiom.get_usage_revision(self.USAGE_ID)

        # Initialise a buffer for the usage's contents to be read into and unpacked/packed
        self._usage_binary_data = [0] * self.u31_PAGE_0_LEN

        # To handle different usage revisions, there are different methods that handle
        # register initialisation (in this python class), dumping out the contents of
        # a usage and unpacking and packing the usage's variables back into binary formats.
        # Use the getattr() find find the appropiate methods that pertain the usage revision.
        self._init_registers   = getattr(self, "_init_registers_uifrev{}".format( self._usage_revision), None)
        self._print_registers  = getattr(self, "_print_registers_uifrev{}".format(self._usage_revision), None)
        self._unpack_registers = getattr(self, "_unpack_uifrev{}".format(         self._usage_revision), None)

        # Raise an exception if an unsupported version of the usage is found.
        if (self._init_registers   is None or 
            self._print_registers  is None or 
            self._unpack_registers is None):
            raise Exception("Unsupported revision of {}. Revision: {}".format(self.__class__.__name__, self._usage_revision))

        # Initialise the variables that are supported by this revision of the usage.
        # With new firmware, the usage could be up-revved and new methods will need
        # to be added
        self._init_registers()

        self.max_report_len = 0
        self._usage_table = {}
        self._usage_table_populated = False

        # Populate the registers by reading the device
        if read:
            self.read()

        if read_usage_table:
            self.build_usage_table()

    def read(self):
        self._usage_binary_data = self._axiom._comms.read_page(self.u31_TARGET_ADDRESS, self.u31_PAGE_0_LEN)
        self._unpack()

    def print_device_info(self):
        self._print_registers()

    def get_device_info_short(self):
        device_channel_count =  self.reg_device_id & 0x3FF
        device_variant       = (self.reg_device_id & 0x7C00) >> 10

        fw_status_str = "eng" if self.reg_fw_status == 0 else "prod"
        if (self.reg_fw_major >= 4 and self.reg_fw_minor >= 8):
            fw_ver = "%d.%d.%d-%s %s" % (self.reg_fw_major, self.reg_fw_minor, self.reg_fw_patch, fw_status_str, self.FW_VARIANTS[self.reg_fw_variant])
        else:
            fw_ver = "%d.%02d-%s (RC%d) %s" % (self.reg_fw_major, self.reg_fw_minor, fw_status_str, self.reg_fw_patch, self.FW_VARIANTS[self.reg_fw_variant])

        return "AX%u%c %s" % (device_channel_count, chr(ord('A') + device_variant), fw_ver)

    def _unpack(self):
        self._unpack_registers()

#region u31 Specific Methods
    def build_usage_table(self):
        self.read()

        # Veryify the device is not in bootloader mode
        if self.reg_mode != 0:
            print("Cannot build usage table, aXiom is in bootloader mode")
            self._usage_table_populated = False
            return False

        target_address = self.convert_usage_to_target_address(0x31, 1)
        usage_buffer = self._axiom._comms.read_page(target_address, (self.reg_num_usages * _Usage_Table_Entry.USAGE_TABLE_ENTRY_SIZE))

        for usage in range(0, self.reg_num_usages):
            offset      = usage * _Usage_Table_Entry.USAGE_TABLE_ENTRY_SIZE
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
                if id != self.USAGE_ID:
                    length = ((num_pages - 1) * self.PAGE_SIZE) + (((usage_buffer[offset + 3] & 0x7F) + 1) * 2)
                else:
                    length = self.PAGE_SIZE + (self.reg_num_usages * 6)

            self._usage_table[id] = _Usage_Table_Entry(id, start_page, num_pages, length, max_offset, offset_type, usage_rev)

            if ((self._usage_table[id].is_report) and (length > self.max_report_len)):
                self.max_report_len = length

        self._usage_table_populated = True
        return True
    
    def print_usage_table(self):
        if self._usage_table_populated == True:
            print("Usage Table: ")
            for u in self._usage_table:
                print(self._usage_table[u])
        else:
            print("Usage table not yet initialised")

    def convert_usage_to_target_address(self, usage, page=0):
        target_address = 0
        if(self._usage_table_populated == False and usage == 0x31):
            target_address = 0x0000 + (page << 8)
        else:
            target_address = (self._usage_table[usage].start_page << 8) + (page << 8)
        return target_address
    
    def is_usage_present_on_device(self, usage):
        """
        Determine if a usage is present in the connected device's usage table. Not all usages are present on all
        firmware builds. For instance, the 2D firmware contains a subset of usages that the 3D firmware supports.

        Returns:
        bool: True if the usage is present, otherwise False.
        """
        return usage in self._usage_table
#endregion

#region u31 Usage Name Usage Revision 1
    def _init_registers_uifrev1(self):
        self.reg_device_id      = 0
        self.reg_mode           = 0
        self.reg_fw_major       = 0
        self.reg_fw_minor       = 0
        self.reg_fw_variant     = 0
        self.reg_fw_status      = 0
        self.reg_tcp_rev        = 0
        self.reg_bl_major       = 0
        self.reg_bl_minor       = 0
        self.reg_jedec_id       = 0
        self.reg_num_usages     = 0
        self.reg_silicon_rev    = 0
        self.reg_fw_patch       = 0


    def _unpack_uifrev1(self):
        field0, field1, field2, field3, field4, field5 = struct.unpack("<6H", bytes(bytearray(self._usage_binary_data[0:12])))
        self.reg_device_id   = (field0 & 0x7FFF)
        self.reg_mode        = (field0 & 0x8000) >> 15

        self.reg_fw_major    = (field1 & 0xFF00) >> 8
        self.reg_fw_minor    = (field1 & 0x00FF)

        self.reg_fw_variant  = (field2 & 0x003F)
        self.reg_fw_status   = (field2 & 0x0080) >> 7
        self.reg_tcp_rev     = (field2 & 0xFF00) >> 8

        self.reg_bl_major    = (field3 & 0xFF00) >> 8
        self.reg_bl_minor    = (field3 & 0x00FF)

        self.reg_jedec_id    = field4
        
        self.reg_num_usages  = (field5 & 0x00FF)
        self.reg_silicon_rev = (field5 & 0x0F00) >> 8
        self.reg_fw_patch    = (field5 & 0xF000) >> 12

    def _print_registers_uifrev1(self):
        device_channel_count =  self.reg_device_id & 0x3FF
        device_variant       = (self.reg_device_id & 0x7C00) >> 10

        fw_status_str = "eng" if self.reg_fw_status == 0 else "prod"
        silicon_rev   = chr(0x41 + self.reg_silicon_rev)

        print("u31 Device Information")
        print("  Device ID   : AX%u%c " % (device_channel_count, chr(0x41 + device_variant)))
        if (self.reg_fw_major >= 4 and self.reg_fw_minor >= 8):
            print("  FW Revision : %d.%d.%d-%s %s" % (self.reg_fw_major, self.reg_fw_minor, self.reg_fw_patch, fw_status_str, self.FW_VARIANTS[self.reg_fw_variant]))
        else:
            print("  FW Revision : %d.%02d-%s (RC%d) %s" % (self.reg_fw_major, self.reg_fw_minor, fw_status_str, self.reg_fw_patch, self.FW_VARIANTS[self.reg_fw_variant]))
        print("  BL Revision : %d.%02d" % (self.reg_bl_major, self.reg_bl_minor))
        print("  Silicon     : 0x%04X (Rev %c)" % (self.reg_jedec_id, silicon_rev))
#endregion
