# Copyright (c) 2025 TouchNetix
# 
# This file is part of axiom_tc and is released under the MIT License:
# See the LICENSE file in the root directory of this project or http://opensource.org/licenses/MIT.

class UsageRevisionBase:
    def __init__(self, axiom, usage_id, read=True):
        self._axiom = axiom
        self._usage_id = usage_id
        self._usage_binary_data = [0] * self._axiom.get_usage_length(self._usage_id)
        if read:
            self.read()

    def read(self):
        self._usage_binary_data = self._axiom.read_usage(self._usage_id)
        self.unpack()

    def write(self, write_to_nvm=False):
        self.pack()
        if write_to_nvm:
            self._axiom.u02.send_command(self._axiom.u02.CMD_STOP)
        self._axiom.config_write_usage_to_device(self._usage_id, self._usage_binary_data)
        if write_to_nvm:
            self._axiom.u02.send_command(self._axiom.u02.CMD_SAVE_CONFIG)
        self.read()

    def print(self):
        self.print_registers()

    def unpack(self):
        raise NotImplementedError()

    def pack(self):
        raise NotImplementedError()

    def print_registers(self):
        raise NotImplementedError()
