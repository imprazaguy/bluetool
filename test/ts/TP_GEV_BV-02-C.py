# Disallow mixing legacy and extended advertising commands

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, LEHelper
from bluetool.error import TestError
import bluetool.command as btcmd


class UpperTester(HCIWorker):
    def test_disallow_mixing_cmds(self, cmd1, cmd2, wait_cmd2_complt_evt):
        reset_cmd = btcmd.HCIReset()
        self.helper.send_hci_cmd_wait_cmd_complt_check_status(reset_cmd)
        self.helper.send_hci_cmd_wait_cmd_complt_check_status(cmd1)
        if wait_cmd2_complt_evt:
            evt = self.helper.send_hci_cmd_wait_cmd_complt(cmd2)
        else:
            evt = self.helper.send_hci_cmd_wait_cmd_status(cmd2)
        if evt.status != 0x0C:
            raise TestError(
                'command 0x{:04x} is not disallowed'.format(cmd2.opcode()))

    def main(self):
        self.helper = LEHelper(self.sock)

        # Legacy advertising command -> extened advertising command
        cmd1 = btcmd.HCILESetAdvertisingParameters(
            100, 100, 0, 0, 0, '\x00'*6, 0x7, 0)
        cmd2_list = [
            (btcmd.HCILESetExtendedAdvertisingParameters(
                0, 0x0000, 100, 100, 0x7, 0, 0, '\x00'*6, 0, 0xFF, 0x01, 0,
                0x01, 0x00, 0), 1),
            (btcmd.HCILESetExtendedAdvertisingData(
                0, 3, 0, '\x00\x01\x02\x03\x04\x05\x06\x07'), 1),
            (btcmd.HCILESetExtendedScanResponseData(
                0, 3, 0, '\x00\x01\x02\x03\x04\x05\x06\x07'), 1),
            (btcmd.HCILESetExtendedAdvertisingEnable(0, 0), 1),
            (btcmd.HCILEReadMaximumAdvertisingDataLength(), 1),
            (btcmd.HCILEReadNumberOfSupportedAdvertisingSets(), 1),
            (btcmd.HCILERemoveAdvertisingSet(0), 1),
            (btcmd.HCILEClearAdvertisingSets(), 1),
        ]
        for cmd2, wait_cmd2_complt_evt in cmd2_list:
            self.test_disallow_mixing_cmds(cmd1, cmd2, wait_cmd2_complt_evt)

        # Extended advertising command -> legacy advertising command
        cmd1 = btcmd.HCILESetExtendedAdvertisingParameters(
            0, 0x0000, 100, 100, 0x7, 0, 0, '\x00'*6, 0, 0xFF, 0x01, 0, 0x01,
            0x00, 0)
        cmd2_list = [
            (btcmd.HCILESetAdvertisingParameters(
                100, 100, 0, 0, 0, '\x00'*6, 0x7, 0), 1),
            (btcmd.HCILEReadAdvertisingChannelTxPower(), 1),
            (btcmd.HCILESetAdvertisingData(
                '\x00\x01\x02\x03\x04\x05\x06\x07'), 1),
            (btcmd.HCILESetScanResponseData(
                '\x00\x01\x02\x03\x04\x05\x06\x07'), 1),
            (btcmd.HCILESetAdvertiseEnable(0), 1),
        ]
        for cmd2, wait_cmd2_complt_evt in cmd2_list:
            self.test_disallow_mixing_cmds(cmd1, cmd2, wait_cmd2_complt_evt)

        # Legacy scan command -> extended scan command
        cmd1 = btcmd.HCILESetScanParameters(1, 200, 20, 0, 0)
        cmd2_list = [
            (btcmd.HCILESetExtendedScanParameters(0, 0, 0x1, 1, 200, 20), 1),
            (btcmd.HCILESetExtendedScanEnable(0, 0, 0, 0), 1),
            (btcmd.HCILEExtendedCreateConnection(
                1, 0, 0, '\x00'*6, 0x1, 100, 20, 15, 15, 0, 50, 10, 10), 0),
        ]
        for cmd2, wait_cmd2_complt_evt in cmd2_list:
            self.test_disallow_mixing_cmds(cmd1, cmd2, wait_cmd2_complt_evt)

        # Extended scan command -> legacy scan command
        cmd1 = btcmd.HCILESetExtendedScanParameters(0, 0, 0x1, 1, 200, 20)
        cmd2_list = [
            (btcmd.HCILESetScanParameters(1, 200, 20, 0, 0), 1),
            (btcmd.HCILESetScanEnable(0, 0), 1),
            (btcmd.HCILECreateConnection(
                100, 20, 1, 0, '\x00'*6, 0, 15, 15, 0, 50, 10, 10), 0),
        ]
        for cmd2, wait_cmd2_complt_evt in cmd2_list:
            self.test_disallow_mixing_cmds(cmd1, cmd2, wait_cmd2_complt_evt)


class Tester(HCICoordinator):
    def main(self):
        pass


bluetest = {
    'coordinator': Tester,
    'worker': [
        ('upper_tester', UpperTester)
    ]
}

if __name__ == "__main__":
    bluetool.log_to_stream()
    bluetool.run_config(bluetest, [1])
