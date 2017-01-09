# Test that an IUT as master can complete the encryption start procedure
# correctly if an unexpected data channel PDU is received.

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, LEHelper
from bluetool.error import TestError
import bluetool.bluez as bluez
import bluetool.command as btcmd
import time

CONN_TIMEOUT_MS = 10000

LTK = '\xbf\x01\xfb\x9d\x4e\xf3\xbc\x36\xd8\x74\xf5\x39\x41\x38\x68\x4c'
EDIV = 0x2474
RAND = 0xABCDEF1234567890


class UpperTester(HCIWorker):
    def main(self):
        peer_addr = self.recv()

        helper = LEHelper(self.sock)
        helper.reset()
        helper.create_connection_by_peer_addr(
            0, peer_addr, 500, 0, 300, 10)
        evt = helper.wait_connection_complete()
        if (evt.status != 0):
            raise TestError('connection fail: status: 0x{:02x}'.format(
                evt.status))
        conn_handle = evt.conn_handle

        # Synchronization of encryption complete
        self.wait()

        cmd = btcmd.HCILEStartEncryption(conn_handle, RAND, EDIV, LTK)
        helper.send_hci_cmd_wait_cmd_status_check_status(cmd)

        evt = helper.wait_encryption_change(conn_handle)
        if evt.status != 0 or evt.enc_enabled != 1:
            raise TestError(
                'encryption failed: status:{}, enabled:{}'.format(
                    evt.status, evt.enc_enabled))

        time.sleep(60)
        cmd = btcmd.HCIDisconnect(conn_handle, 0x13)
        helper.send_hci_cmd_wait_cmd_status_check_status(cmd)
        helper.wait_disconnection_complete(conn_handle)


class LowerTester(HCIWorker):
    def main(self):
        helper = LEHelper(self.sock)
        helper.reset()
        helper.start_advertising(0xA0)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise TestError('connection fail: status: 0x{:02x}'.format(
                evt.status))
        conn_handle = evt.conn_handle

        # Synchronization of encryption complete
        self.signal()

        print 'lower tester connection created: {}'.format(conn_handle)

        helper.wait_le_event(bluez.EVT_LE_LTK_REQUEST)
        cmd = btcmd.HCILELongTermKeyRequestReply(conn_handle, LTK)
        helper.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        evt = helper.wait_encryption_change(conn_handle)
        if evt.status != 0 or evt.enc_enabled != 1:
            raise TestError(
                'encryption failed: status:{}, enabled:{}'.format(
                    evt.status, evt.enc_enabled))

        helper.wait_disconnection_complete(conn_handle)


class Tester(HCICoordinator):
    def main(self):
        # Exchange peer addresses
        self.upper_tester.send(self.lower_tester.bd_addr)

        # Synchronization of encryption completion
        self.lower_tester.wait()
        self.upper_tester.signal()


bluetest = {
    'coordinator': Tester,
    'worker': [
        ('upper_tester', UpperTester),
        ('lower_tester', LowerTester)
    ]
}

if __name__ == "__main__":
    bluetool.log_to_stream()
    bluetool.run_config(bluetest, [1, 0])
