"""Test white list add/remove
"""
from bluetool.core import HCICoordinator, HCISock, HCIFilter, HCIWorker, HCITask
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
    def __init__(self, hci_sock, peer_addr):
        super(WhiteListMaster, self).__init__(hci_sock)
        self.peer_addr = peer_addr

    def run(self):
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT).all_events())

        if ResetTask(self.sock).reset() != 0:
            return

        cmd = btcmd.HCILEAddDeviceToWhiteList(0, self.peer_addr)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 'm: HCI_LE_ADD_DEVICE_TO_WHITE_LIST failed: {}'.format(evt.status)
            return

        cmd = btcmd.HCILECreateConnection(96, 24, 1, 0, '\x00'*6, 0, 6, 12, 0, 100, 0, 0)
        evt = self.send_hci_cmd_wait_cmd_status(cmd)
        if evt.status != 0:
            print 'm: HCI_LE_CREATE_CONNECTION failed: {}'.format(evt.status)
            return

        evt = self.recv_hci_evt()
        if evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE:
            print 'm: connect to {}'.format(ba2str(evt.peer_addr))

class WhiteListSlave(HCIWorker):
    def __init__(self, hci_sock, peer_addr):
        super(WhiteListSlave, self).__init__(hci_sock)
        self.peer_addr = peer_addr

    def run(self):
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT).all_events())

        if ResetTask(self.sock).reset() != 0:
            return

        cmd = btcmd.HCILESetAdvertisingParameters(0xA0, 0xA0, 0, 0, 0, '\x00'*6, 0x7, 0)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 's: HCI_SET_ADV_PARAMS failed: {}'.format(evt.status)
            return

        cmd = btcmd.HCILESetAdvertiseEnable(1)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 's: HCI_SET_ADV_ENABLE failed: {}'.format(evt.status)
            return

        evt = self.recv_hci_evt()
        if evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE:
            print 's: connect to {}'.format(ba2str(evt.peer_addr))

        cmd = btcmd.HCILESetAdvertiseEnable(0)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            print 's: cannot disable advertising: {}'.format(evt.status)


class WhiteListTester(HCICoordinator):
    def __init__(self):
        super(WhiteListTester, self).__init__(0, 1)
        self.worker = [None]*2
        self.worker[0] = WhiteListMaster(self.sock[0], self.bd_addr[1])
        self.worker[1] = WhiteListSlave(self.sock[1], self.bd_addr[0])

    def main(self):
        print 'master[{}], slave[{}]'.format(ba2str(self.bd_addr[0]), ba2str(self.bd_addr[1]))
        self.worker[0].start()
        self.worker[1].start()
        self.worker[0].join()
        self.worker[1].join()

if __name__ == "__main__":
    tester = WhiteListTester()
    tester.main()
