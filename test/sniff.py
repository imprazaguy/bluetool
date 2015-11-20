# Test transmitting data after exiting sniff mode
import time

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, HCIWorkerProxy, HCITask, BREDRHelper
from bluetool.bluez import ba2str
from bluetool.error import HCICommandError, TestError, HCITimeoutError
import bluetool.bluez as bluez
import bluetool.command as btcmd
import bluetool.event as btevt
from bluetool.data import HCIACLData

CONN_TIMEOUT_MS = 10000
HCI_ACL_MAX_SIZE = 27
NUM_ACL_DATA = 1600

class LegacyMaster(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LegacyMaster, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

    def create_test_acl_data(self, num_acl_data=NUM_ACL_DATA):
        data = [None]*num_acl_data
        data_i = 0
        for i in xrange(0, num_acl_data):
            data[i] = HCIACLData(self.conn_handle, 0x1, 0x0,
                    ''.join(chr(c & 0xff) for c in xrange(data_i, data_i + HCI_ACL_MAX_SIZE)))
            data_i = (data_i + 1) % 256
        return data

    def main(self):
        helper = BREDRHelper(self.sock)

        try:
            helper.reset()
        except HCICommandError as err:
            self.log.warning('cannot reset', exc_info=True)
            return

        helper.create_connection_by_peer_addr(self.peer_addr)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
        self.conn_handle = evt.conn_handle
        self.log.info('connect to %s', ba2str(evt.bd_addr))
        self.wait() # Wait slave to connect

        helper.write_link_policy(self.conn_handle, 0x5)
        self.send(True)
        self.wait()

        helper.wait_hci_evt(lambda evt: evt.code == bluez.EVT_MODE_CHANGE) # Wait to enter LPS (sniff mode)

        helper.wait_hci_evt(lambda evt: evt.code == bluez.EVT_MODE_CHANGE) # Wait to exit LPS (active mode)
        self.send(True) # tell exiting sniff mode

        while True:
            num_acl_data = self.recv()
            if num_acl_data <= 0:
                break
            try:
                i = 0
                while i < num_acl_data:
                    pkt_type, pkt = self.recv_hci_pkt()
                    if pkt_type == bluez.HCI_ACLDATA_PKT:
                        print i, pkt
                        i = i + 1
                        self.send(True) # tell that ACL data are successfully received
                    else:
                        self.log.info('ptype: {}, {}'.format(pkt_type, pkt))
            except (HCICommandError, HCITimeoutError):
                self.log.warning('fail to connect to initiator', exc_info=True)

        helper.disconnect(self.conn_handle, 0x13)
        helper.wait_disconnection_complete(self.conn_handle)


class LegacySlave(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LegacySlave, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr
        self.num_acl_tx_not_acked = 0

    def create_test_acl_data(self, num_acl_data=NUM_ACL_DATA):
        data = [None]*num_acl_data
        data_i = 0
        for i in xrange(0, num_acl_data):
            data[i] = HCIACLData(self.conn_handle, 0x1, 0x0,
                    ''.join(chr(c & 0xff) for c in xrange(data_i, data_i + HCI_ACL_MAX_SIZE)))
            data_i = (data_i + 1) % 256
        return data

    def main(self):
        helper = BREDRHelper(self.sock)

        try:
            helper.reset()
            #self.setup_h2c_flow_control()
        except HCICommandError:
            self.log.warning('cannot reset', exc_info=True)
            return

        helper.accept_connection()
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
        self.conn_handle = evt.conn_handle
        self.log.info('connect to %s', ba2str(evt.bd_addr))
        self.send(True) # trigger master to send data

        helper.write_link_policy(self.conn_handle, 0x5)
        self.send(True)
        self.wait()

        helper.sniff_mode(self.conn_handle, 996, 996, 10, 10)
        helper.wait_hci_evt(lambda evt: evt.code == bluez.EVT_MODE_CHANGE)

        time.sleep(20) # Wait to enter LPS

        helper.exit_sniff_mode(self.conn_handle)
        helper.wait_hci_evt(lambda evt: evt.code == bluez.EVT_MODE_CHANGE)

        self.wait() # Wait for remote device to exit sniff mode
        #time.sleep(1)
        self.send(True) # Signal to send data

        while True:
            num_acl_data = self.recv()
            if num_acl_data <= 0:
                break
            try:
                data = self.create_test_acl_data(num_acl_data)
                for d in data:
                    self.send_acl_data(d)
                    self.wait() # Wait for remote device to receive data
            except (HCICommandError, TestError):
                self.log.warning('fail to create connection by white list', exc_info=True)

        helper.wait_disconnection_complete(self.conn_handle, CONN_TIMEOUT_MS)


class LegacyTester(HCICoordinator):
    def __init__(self):
        super(LegacyTester, self).__init__()
        self.worker.append(HCIWorkerProxy(0, self, LegacyMaster))
        self.worker.append(HCIWorkerProxy(1, self, LegacySlave))
        self.worker[0].worker.peer_addr = self.worker[1].bd_addr
        self.worker[1].worker.peer_addr = self.worker[0].bd_addr

    def main(self):
        print 'master[{}], slave[{}]'.format(ba2str(self.worker[0].bd_addr), ba2str(self.worker[1].bd_addr))

        # Wait connection establishment
        self.worker[1].recv()
        self.worker[0].signal()

        # Wait write link policy working
        self.worker[0].recv()
        self.worker[1].recv()
        self.worker[0].signal()
        self.worker[1].signal()

        # Wait for remote device to exit sniff mode
        self.worker[0].recv()
        self.worker[1].signal()

        # Wait to send data
        self.worker[1].recv()

        num_acl_data = 100
        self.worker[0].send(num_acl_data)
        self.worker[1].send(num_acl_data)
        for i in xrange(0, num_acl_data):
            self.worker[0].recv()
            self.worker[1].signal()

        self.worker[0].send(0)
        self.worker[1].send(0)


if __name__ == "__main__":
    bluetool.log_to_stream()
    tester = LegacyTester()
    tester.run()

