"""Test white list add/remove
"""
import multiprocessing as mp
import time

from bluetool.core import HCICoordinator, HCIFilter, HCIWorker, HCIWorkerProxy, HCITask
from bluetool.bluez import ba2str
from bluetool.error import HCICommandError, TestError
import bluetool.bluez as bluez
import bluetool.command as btcmd
import bluetool.event as btevt

class ResetTask(HCITask):
    def __init__(self, hci_sock):
        super(ResetTask, self).__init__(hci_sock)

    def reset(self):
        cmd = btcmd.HCIReset()
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

        cmd = btcmd.HCISetEventMask(0x20001FFFFFFFFFFFL)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

        cmd = btcmd.HCILEClearWhiteList()
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

class WhiteListMaster(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(WhiteListMaster, self).__init__(hci_sock, pipe)
        self.peer_addr = peer_addr

    def main(self):
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT).all_events())

        try:
            ResetTask(self.sock).reset()
        except HCICommandError as err:
            self.log.warning('cannot reset', exc_info=True)
            return

        while True:
            going = self.recv()
            if not going:
                break

            # Case 1: Test initiator connects to an advertiser with bd_addr in white list.
            try:
                self.add_device_to_white_list(0, self.peer_addr)
                self.test_create_connect_by_white_list(None)
                self.remove_device_from_white_list(0, self.peer_addr)
                succeeded = True
            except HCICommandError:
                self.log.warning('fail to create connection by white list', exc_info=True)
                succeeded = False
            self.send(succeeded)
            self.wait()

            # Case 2: Test initiator connects to an advertiser with bd_addr not in white list.
            try:
                try:
                    self.test_create_connect_by_white_list(3000)
                    raise TestError('connect to device not in white list')
                except HCITimeoutError:
                    pass
                self.create_connect_cancel()
                succeeded = True
            except (HCICommandError, TestError):
                self.log.warning('fail to prohibit connection creation by white list', exc_info=True)
                succeeded = False
            self.send(succeeded)

    def add_device_to_white_list(self, peer_addr_type, peer_addr):
        cmd = btcmd.HCILEAddDeviceToWhiteList(peer_addr_type, peer_addr)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def remove_device_from_white_list(self, peer_addr_type, peer_addr):
        cmd = btcmd.HCILERemoveDeviceFromWhiteList(peer_addr_type, self.peer_addr)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def test_create_connect_by_white_list(self, timeout):
        cmd = btcmd.HCILECreateConnection(96, 24, 1, 0, '\x00'*6, 0, 6, 12, 0, 100, 0, 0)
        evt = self.send_hci_cmd_wait_cmd_status(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

        self.conn_handle = -1
        while True:
            evt = self.recv_hci_evt(timeout)
            if evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE:
                if evt.status != 0:
                    raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
                self.conn_handle = evt.conn_handle
                self.log.info('connect to %s', ba2str(evt.peer_addr))
                break
            else:
                self.log.info('ignore event: %d', evt.code)

        time.sleep(1)

        cmd = btcmd.HCIDisconnect(self.conn_handle, 0x13)
        evt = self.send_hci_cmd_wait_cmd_status(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

        while True:
            evt = self.recv_hci_evt()
            if evt.code == bluez.EVT_DISCONN_COMPLETE and evt.conn_handle == self.conn_handle:
                break
            else:
                self.log.info('ignore event: %d', evt.code)

    def create_connect_cancel(self):
        cmd = btcmd.HCILECreateConnectionCancel()
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

class WhiteListSlave(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(WhiteListSlave, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

    def main(self):
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT).all_events())

        try:
            ResetTask(self.sock).reset()
        except HCICommandError:
            self.log.warning('cannot reset', exc_info=True)
            return

        while True:
            going = self.recv()
            if not going:
                break

            # Case 1: Test connect to an initiator with advertiser's bd_addr in white list.
            try:
                self.test_connect_initiator(None)
                self.wait_disconnection()
                succeeded = True
            except HCICommandError:
                self.log.warning('fail to connect to initiator', exc_info=True)
                succeeded = False
            self.send(succeeded)
            self.wait()

            # Case 2: Test connect to an initiator without advertiser's bd_addr in white list.
            try:
                try:
                    self.test_connect_initiator(3000)
                    raise TestError('device not in white list connects to initiator')
                except HCITimeoutError:
                    pass
                succeeded = True
            except HCICommandError:
                self.log.warning('fail to prohibit connection creation by white list', exc_info=True)
                succeeded = False
            self.send(succeeded)


    def test_connect_initiator(self, timeout):
        cmd = btcmd.HCILESetAdvertisingParameters(0xA0, 0xA0, 0, 0, 0, '\x00'*6, 0x7, 0)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

        cmd = btcmd.HCILESetAdvertiseEnable(1)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

        self.conn_handle = -1
        while True:
            evt = self.recv_hci_evt(timeout)
            if evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE:
                if evt.status != 0:
                    raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
                self.conn_handle = evt.conn_handle
                self.log.info('connect to %s', ba2str(evt.peer_addr))
                break
            else:
                self.log.info('ignore event: %d', evt.code)

        cmd = btcmd.HCILESetAdvertiseEnable(0)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def wait_disconnection(self):
        while True:
            evt = self.recv_hci_evt()
            if evt.code == bluez.EVT_DISCONN_COMPLETE and evt.conn_handle == self.conn_handle:
                break
            else:
                self.log.info('ignore event: %d', evt.code)

class WhiteListTester(HCICoordinator):
    def __init__(self):
        super(WhiteListTester, self).__init__()
        self.worker.append(HCIWorkerProxy(0, self, WhiteListMaster))
        self.worker.append(HCIWorkerProxy(1, self, WhiteListSlave))
        self.worker[0].worker.peer_addr = self.worker[1].bd_addr
        self.worker[1].worker.peer_addr = self.worker[0].bd_addr

    def main(self):
        print 'master[{}], slave[{}]'.format(ba2str(self.worker[0].bd_addr), ba2str(self.worker[1].bd_addr))
        
        n_run = 10
        n_case1_success = 0
        n_case2_success = 0
        for i in xrange(0, n_run):
            # Start test
            self.worker[0].send(True)
            self.worker[1].send(True)

            # Case 1.
            master_succeeded = self.worker[0].recv()
            slave_succeeded = self.worker[1].recv()
            if master_succeeded and slave_succeeded:
                n_case1_success += 1

            self.worker[0].signal()
            self.worker[1].signal()
            # Case 2.
            master_succeeded = self.worker[0].recv()
            slave_succeeded = self.worker[1].recv()
            if master_succeeded and slave_succeeded:
                n_case2_success += 1

        # Stop test
        self.worker[0].send(False) 
        self.worker[1].send(False)

        print 'case 1 #success: {}/{}'.format(n_case1_success, n_run)
        print 'case 2 #success: {}/{}'.format(n_case2_success, n_run)


if __name__ == "__main__":
    tester = WhiteListTester()
    tester.run()

