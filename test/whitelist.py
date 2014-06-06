"""Test white list add/remove
"""
import multiprocessing as mp
import time

from bluetool.core import HCICoordinator, HCIFilter, HCIWorker, HCIWorkerProxy, HCITask
from bluetool.bluez import ba2str
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
            print 'm: HCI_RESET failed: {}'.format(evt.status)
            return -1

        cmd = btcmd.HCISetEventMask(0x20001FFFFFFFFFFFL)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 'm: HCI_SET_EVENT_MASK failed: {}'.format(evt.status)
            return -1

        cmd = btcmd.HCILEClearWhiteList()
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 'm: HCI_LE_CLEAR_WHITE_LIST failed: {}'.format(evt.status)
            return -1
        return 0

class WhiteListMaster(HCIWorker):
    def __init__(self, hci_sock, pipe, peer_addr=None):
        super(WhiteListMaster, self).__init__(hci_sock, pipe)
        self.peer_addr = peer_addr

    def run(self):
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT).all_events())

        if ResetTask(self.sock).reset() != 0:
            return False

        while True:
            going = self.recv()
            if not going:
                break

            succeeded = self.test_connect_slave_in_wlist()
            self.send(succeeded)

    def test_connect_slave_in_wlist(self):
        cmd = btcmd.HCILEAddDeviceToWhiteList(0, self.peer_addr)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 'm: HCI_LE_ADD_DEVICE_TO_WHITE_LIST failed: {}'.format(evt.status)
            return False

        cmd = btcmd.HCILECreateConnection(96, 24, 1, 0, '\x00'*6, 0, 6, 12, 0, 100, 0, 0)
        evt = self.send_hci_cmd_wait_cmd_status(cmd)
        if evt.status != 0:
            print 'm: HCI_LE_CREATE_CONNECTION failed: {}'.format(evt.status)
            return False

        conn_handle = -1
        evt = self.recv_hci_evt()
        if evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE:
            conn_handle = evt.conn_handle
            print 'm: connect to {}'.format(ba2str(evt.peer_addr))

            time.sleep(1)
            cmd = btcmd.HCIDisconnect(conn_handle, 0x16)
            evt2 = self.send_hci_cmd_wait_cmd_status(cmd)
            if evt2.status != 0:
                print 'm: disconnection failed: {}'.format(evt2.status)
                return False

            evt2 = self.recv_hci_evt()
            if evt2.code == bluez.EVT_DISCONN_COMPLETE and evt2.conn_handle == conn_handle:
                cmd = btcmd.HCILERemoveDeviceFromWhiteList(0, self.peer_addr)
                evt3 = self.send_hci_cmd_wait_cmd_complt(cmd)
                if evt3.status != 0:
                    print 'm: HCI_LE_REMOVE_DEVICE_FROM_WHITE_LIST failed: {}'.format(evt3.status)
                    return False

        return True

class WhiteListSlave(HCIWorker):
    def __init__(self, hci_sock, pipe, peer_addr=None):
        super(WhiteListSlave, self).__init__(hci_sock, pipe)
        self.peer_addr = peer_addr

    def run(self):
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT).all_events())

        if ResetTask(self.sock).reset() != 0:
            return False

        while True:
            going = self.recv()
            if not going:
                break

            succeeded = self.test_connect_master()
            self.send(succeeded)

    def test_connect_master(self):
        cmd = btcmd.HCILESetAdvertisingParameters(0xA0, 0xA0, 0, 0, 0, '\x00'*6, 0x7, 0)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 's: HCI_SET_ADV_PARAMS failed: {}'.format(evt.status)
            return False

        cmd = btcmd.HCILESetAdvertiseEnable(1)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 's: HCI_SET_ADV_ENABLE failed: {}'.format(evt.status)
            return False

        conn_handle = -1
        evt = self.recv_hci_evt()
        if evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE:
            conn_handle = evt.conn_handle
            print 's: connect to {}'.format(ba2str(evt.peer_addr))

        cmd = btcmd.HCILESetAdvertiseEnable(0)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 's: cannot disable advertising: {}'.format(evt.status)
            return False

        evt = self.recv_hci_evt()
        if evt.code == bluez.EVT_DISCONN_COMPLETE and evt.conn_handle != conn_handle:
            print 's: cannot disconnect'
            return False
        return True


class WhiteListTester(HCICoordinator):
    def __init__(self):
        super(WhiteListTester, self).__init__()
        self.worker = [None]*2
        self.worker[0] = HCIWorkerProxy(0, WhiteListMaster)
        self.worker[1] = HCIWorkerProxy(1, WhiteListSlave)
        self.worker[0].worker.peer_addr = self.worker[1].bd_addr
        self.worker[1].worker.peer_addr = self.worker[0].bd_addr

    def main(self):
        print 'master[{}], slave[{}]'.format(ba2str(self.worker[0].bd_addr), ba2str(self.worker[1].bd_addr))
        for w in self.worker:
            w.start()
        
        n_run = 10
        n_success = 0
        for i in xrange(0, n_run):
            # Start test
            self.worker[0].send(True)
            self.worker[1].send(True)

            # Receive success or failure
            master_succeeded = self.worker[0].recv()
            slave_succeeded = self.worker[1].recv()
            if master_succeeded and slave_succeeded:
                n_success += 1

        # Stop test
        self.worker[0].send(False) 
        self.worker[1].send(False)

        print '#success: {}/{}'.format(n_success, n_run)

        for w in self.worker:
            w.join()

if __name__ == "__main__":
    tester = WhiteListTester()
    tester.main()

