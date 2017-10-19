# TP/CON/SLA/BV-40-C [Slave Data Length Update - Data length update not
# supported by Tester]
#
# Verify that the IUT as Slave correctly handles communication with a Lower
# Tester that does not support the Data Length Update Procedure

import time

import bluetool
from bluetool.core import HCIDataTransCoordinator, HCIDataTransWorker, LEHelper
import bluetool.command as btcmd
import bluetool.error as bterr
from bluetool.utils import bytes2str

CONN_TIMEOUT_MS = 10000


class IUT(HCIDataTransWorker):
    def main(self):
        helper = LEHelper(self.sock)

        helper.reset()
        cmd = btcmd.HCILEWriteSuggestedDefaultDataLength(251, (251+14)*8)
        helper.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        helper.start_advertising(0xA0)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise bterr.TestError(
                'connection fail: status: 0x{:02x}'.format(evt.status))
        self.log.info('connect to %s', bytes2str(evt.peer_addr))
        conn_handle = evt.conn_handle

        self.send(conn_handle)

        self.wait()  # Wait lower tester to connect and reject LL_LENGTH_REQ

        self.test_acl_trans_send(CONN_TIMEOUT_MS / 1000)

        helper.disconnect(conn_handle, 0x13)
        helper.wait_disconnection_complete(conn_handle)


class LowerTester(HCIDataTransWorker):
    def main(self):
        peer_addr = self.recv()

        helper = LEHelper(self.sock)

        helper.reset()

        helper.create_connection_by_peer_addr(0, peer_addr, 60, 0, 200, 50)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise bterr.TestError(
                'connection fail: status: 0x{:02x}'.format(evt.status))
        self.log.info('connect to %s', bytes2str(evt.peer_addr))
        conn_handle = evt.conn_handle

        self.send(conn_handle)

        self.test_acl_trans_recv(CONN_TIMEOUT_MS / 1000)

        helper.wait_disconnection_complete(conn_handle, CONN_TIMEOUT_MS)


class TestManager(HCIDataTransCoordinator):
    def main(self):
        self.lt.send(self.iut.bd_addr)

        send_conn_handle = self.iut.recv()
        recv_conn_handle = self.lt.recv()
        time.sleep(1)  # Wait for data length update procedure to finish
        self.iut.signal()

        acl_list = self.create_test_acl_data(send_conn_handle, 1, 251)
        succeeded = self.test_acl_trans(self.iut, self.lt, recv_conn_handle,
                                        acl_list, CONN_TIMEOUT_MS / 1000)

        self.iut.send(0)
        self.lt.send(0)
        if succeeded:
            return 0
        return 1


bluetest = {
    'coordinator': TestManager,
    'worker': [
        ('iut', IUT),
        ('lt', LowerTester)
    ]
}


if __name__ == "__main__":
    bluetool.log_to_stream()
    bluetool.run_config(bluetest, [0, 1])
