# TP/CCO/BV-09-C [LE Set Data Length]
#
# Verify that the IUT correctly handles the LE Set Data Legnth Command

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, LEHelper
import bluetool.bluez as bluez
import bluetool.error as bterr
from bluetool.utils import bytes2str

CONN_TIMEOUT_MS = 10000


class IUT(HCIWorker):
    def main(self):
        peer_addr = self.recv()

        helper = LEHelper(self.sock)

        helper.reset()

        helper.create_connection_by_peer_addr(0, peer_addr, 60, 0, 200, 50)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise bterr.TestError(
                'connection fail: status: 0x{:02x}'.format(evt.status))
        conn_handle = evt.conn_handle
        self.log.info('connect to %s', bytes2str(evt.peer_addr))

        helper.set_data_len(conn_handle, 251)
        helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)

        helper.disconnect(conn_handle, 0x13)
        helper.wait_disconnection_complete(conn_handle, CONN_TIMEOUT_MS)


class LowerTester(HCIWorker):
    def main(self):
        helper = LEHelper(self.sock)

        helper.reset()

        helper.start_advertising(0xA0)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise bterr.TestError(
                'connection fail: status: 0x{:02x}'.format(evt.status))
        conn_handle = evt.conn_handle
        self.log.info('connect to %s', bytes2str(evt.peer_addr))

        helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)
        helper.wait_disconnection_complete(conn_handle, CONN_TIMEOUT_MS)


class TestManager(HCICoordinator):
    def main(self):
        self.iut.send(self.lt.bd_addr)


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
