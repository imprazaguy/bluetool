# Test LE ACL data transmission from master to slave.

import time

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, HCIWorkerProxy, HCITask, LEHelper
from bluetool.bluez import ba2str
from bluetool.error import HCICommandError, TestError, HCITimeoutError
import bluetool.bluez as bluez
import bluetool.command as btcmd
import bluetool.event as btevt
from bluetool.data import HCIACLData

CONN_TIMEOUT_MS = 10000
HCI_ACL_MAX_SIZE = 27
NUM_ACL_DATA = 1600

class LEDataSender(HCITask):
    """Helper to provide flow control for sending LE ACL data"""

    def __init__(self, hci_sock):
        super(LEDataSender, self).__init__(hci_sock)
        self.num_acl_tx_not_acked = 0

    def setup_h2c_flow_control(self):
        evt = LEHelper(self.sock).read_buffer_size()
        self.hc_le_acl_data_pkt_len = evt.hc_le_acl_data_pkt_len
        self.hc_total_num_le_acl_data_pkts = evt.hc_total_num_le_acl_data_pkts
        self.log.info('acl_data_pkt_len=%d, #acl_data_pkts=%d',
                self.hc_le_acl_data_pkt_len,
                self.hc_total_num_le_acl_data_pkts)

    def send_acl_data(self, acl_data):
        while self.num_acl_tx_not_acked >= self.hc_total_num_le_acl_data_pkts:
            evt = self.wait_hci_evt(lambda evt: evt.code == bluez.EVT_NUM_COMP_PKTS)
            tx_acked = sum(evt.num_completed_pkts)
            self.num_acl_tx_not_acked -= tx_acked
        super(LEDataSender, self).send_acl_data(acl_data)
        self.num_acl_tx_not_acked += 1
        try:
            evt = self.wait_hci_evt(lambda evt: evt.code == bluez.EVT_NUM_COMP_PKTS,
                    0)
            tx_acked = sum(evt.num_completed_pkts)
            self.num_acl_tx_not_acked -= tx_acked
        except HCITimeoutError:
            pass

class LEMaster(HCIWorker, LEDataSender):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LEMaster, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

    def main(self):
        helper = LEHelper(self.sock)

        try:
            helper.reset()
            self.setup_h2c_flow_control()
        except HCICommandError as err:
            self.log.warning('cannot reset', exc_info=True)
            return

        helper.add_device_to_white_list(0, self.peer_addr)
        helper.create_connection_by_white_list(12, 0, 200, 11)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
        conn_handle = evt.conn_handle
        self.send(conn_handle)
        self.log.info('connect to %s', ba2str(evt.peer_addr))
        self.wait() # Wait slave to connect

        # Send ACL data
        keep_send_data = True
        while keep_send_data:
            num_acl_data = self.recv()
            if num_acl_data <= 0:
                break

            for i in xrange(0, num_acl_data):
                data = self.recv()
                self.send_acl_data(data)
                succeeded = self.recv() # Wait for slave to receive correct data
                if not succeeded:
                    keep_send_data = False
                    break

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
        self.send(True) # trigger master to send data

        # Receive ACL data
        while True:
            num_acl_data = self.recv()
            if num_acl_data <= 0:
                break
            try:
                i = 0
                while i < num_acl_data:
                    pkt_type, pkt = self.recv_hci_pkt()
                    if pkt_type == bluez.HCI_ACLDATA_PKT:
                        i = i + 1
                        self.send(pkt.data)
                        succeeded = self.recv() # If data received are correct
                    else:
                        self.log.info('Ignore ptype: {}, {}'.format(pkt_type, pkt))
            except (HCICommandError, HCITimeoutError):
                self.log.warning('fail to receive ACL data from master', exc_info=True)

        helper.wait_disconnection_complete(conn_handle, CONN_TIMEOUT_MS)


class LETester(HCICoordinator):
    def __init__(self):
        super(LETester, self).__init__()
        self.worker.append(HCIWorkerProxy(0, self, LEMaster))
        self.worker.append(HCIWorkerProxy(1, self, LESlave))
        self.worker[0].worker.peer_addr = self.worker[1].bd_addr
        self.worker[1].worker.peer_addr = self.worker[0].bd_addr

    def create_test_acl_data(self, conn_handle, num_acl_data=NUM_ACL_DATA):
        data = [None]*num_acl_data
        data_i = 0
        for i in xrange(0, num_acl_data):
            data[i] = HCIACLData(conn_handle, 0x1, 0x0,
                    ''.join(chr(c & 0xff) for c in xrange(data_i, data_i + HCI_ACL_MAX_SIZE)))
            data_i = (data_i + 1) % 256
        return data

    def main(self):
        print 'master[{}], slave[{}]'.format(ba2str(self.worker[0].bd_addr), ba2str(self.worker[1].bd_addr))

        conn_handle = self.worker[0].recv()
        # Wait connection establishment
        self.worker[1].recv()
        self.worker[0].signal()

        while True:
            num_acl_data = int(raw_input("Enter #acl_data to send: "))
            self.worker[0].send(num_acl_data)
            self.worker[1].send(num_acl_data)
            if num_acl_data <= 0:
                break

            acl = self.create_test_acl_data(conn_handle, num_acl_data)
            for i in xrange(0, num_acl_data):
                print i, acl[i]
                self.worker[0].send(acl[i])
                data_received = self.worker[1].recv()
                succeeded = (acl[i].data == data_received)
                self.worker[0].send(succeeded)
                self.worker[1].send(succeeded)
                if not succeeded:
                    self.log.warning("incorrect data received: {}".format(data_received))
                    break

if __name__ == "__main__":
    bluetool.log_to_stream()
    tester = LETester()
    tester.run()

