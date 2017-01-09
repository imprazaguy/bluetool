# Test LE ACL data transmission from master to slave.

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, HCIWorkerProxy, HCITask, LEHelper
from bluetool.bluez import ba2str
from bluetool.error import HCICommandError, TestError, HCITimeoutError
import bluetool.bluez as bluez
import bluetool.command as btcmd
import bluetool.event as btevt
from bluetool.data import HCIACLData
from bluetool.utils import bytes2str, htole16

CONN_TIMEOUT_MS = 10000

class LEMaster(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LEMaster, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

    def main(self):
        helper = LEHelper(self.sock)

        try:
            helper.reset()
        except HCICommandError as err:
            self.log.warning('cannot reset', exc_info=True)
            return

        helper.add_device_to_white_list(0, self.peer_addr)
        helper.create_connection_by_white_list(60, 0, 200, 50)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
        conn_handle = evt.conn_handle
        self.send(conn_handle)
        self.log.info('connect to %s', ba2str(evt.peer_addr))
        self.wait() # Wait slave to connect

        helper.set_data_len(conn_handle, 251)
        helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)

        try:
            helper.disconnect(conn_handle, 0x13)
            helper.wait_disconnection_complete(conn_handle)
        finally:
            helper.remove_device_from_white_list(0, self.peer_addr)


class LESlave(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LESlave, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

    def main(self):
        helper = LEHelper(self.sock)

        try:
            helper.reset()
        except HCICommandError:
            self.log.warning('cannot reset', exc_info=True)
            return

        helper.start_advertising(0xA0)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
        conn_handle = evt.conn_handle
        self.log.info('connect to %s', ba2str(evt.peer_addr))
        self.send(True) # Trigger next step

        helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)

        helper.wait_disconnection_complete(conn_handle, CONN_TIMEOUT_MS)


class LETester(HCICoordinator):
    def __init__(self):
        super(LETester, self).__init__()
        self.worker.append(HCIWorkerProxy(0, self, LEMaster))
        self.worker.append(HCIWorkerProxy(1, self, LESlave))
        self.worker[0].worker.peer_addr = self.worker[1].bd_addr
        self.worker[1].worker.peer_addr = self.worker[0].bd_addr

    def main(self):
        print 'master[{}], slave[{}]'.format(ba2str(self.worker[0].bd_addr), ba2str(self.worker[1].bd_addr))

        conn_handle = self.worker[0].recv()
        # Wait connection establishment
        self.worker[1].recv()
        self.worker[0].signal()

if __name__ == "__main__":
    bluetool.log_to_stream()
    tester = LETester()
    tester.run()

