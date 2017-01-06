# Test LE data transmission

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, LEHelper
from bluetool.bluez import ba2str
from bluetool.error import HCICommandError, TestError, HCITimeoutError
import bluetool.bluez as bluez
from bluetool.data import HCIACLData
import logging

CONN_TIMEOUT_MS = 10000
HCI_ACL_MAX_SIZE = 27
NUM_ACL_DATA = 1600


class LEMaster(HCIWorker):
    def create_test_acl_data(self):
        data = [None]*NUM_ACL_DATA
        data_i = 0
        for i in xrange(0, NUM_ACL_DATA):
            if i % 8 == 0:
                pb_flag = 0x1
            else:
                pb_flag = 0x0
            data[i] = HCIACLData(
                self.conn_handle, pb_flag, 0x0,
                ''.join(chr(c & 0xff) for c in xrange(
                    data_i, data_i + HCI_ACL_MAX_SIZE)))
            data_i = (data_i + 1) % 256
        return data

    def setup_h2c_flow_control(self):
        self.num_acl_tx_not_acked = 0
        evt = LEHelper(self.sock).read_buffer_size()
        self.hc_le_acl_data_pkt_len = evt.hc_le_acl_data_pkt_len
        self.hc_total_num_le_acl_data_pkts = evt.hc_total_num_le_acl_data_pkts
        self.log.info(
            'acl_data_pkt_len=%d, #acl_data_pkts=%d',
            self.hc_le_acl_data_pkt_len,
            self.hc_total_num_le_acl_data_pkts)

    def send_acl_data(self, acl_data):
        while self.num_acl_tx_not_acked >= self.hc_total_num_le_acl_data_pkts:
            evt = self.wait_hci_evt(
                lambda evt: evt.code == bluez.EVT_NUM_COMP_PKTS)
            tx_acked = sum(evt.num_completed_pkts)
            self.num_acl_tx_not_acked -= tx_acked
        super(LEMaster, self).send_acl_data(acl_data)
        self.num_acl_tx_not_acked += 1
        self.log.info('num_acl_tx_not_acked=%d', self.num_acl_tx_not_acked)
        try:
            evt = self.wait_hci_evt(
                lambda evt: evt.code == bluez.EVT_NUM_COMP_PKTS, 0)
            tx_acked = sum(evt.num_completed_pkts)
            self.num_acl_tx_not_acked -= tx_acked
        except HCITimeoutError:
            pass

    def main(self):
        peer_addr = self.recv()

        helper = LEHelper(self.sock)
        helper.reset()
        self.setup_h2c_flow_control()

        while True:
            going = self.recv()
            if not going:
                break

            try:
                helper.add_device_to_white_list(0, peer_addr)
                helper.create_connection_by_white_list(6, 0, 200, 11)
                evt = helper.wait_connection_complete()
                if evt.status != 0:
                    raise TestError(
                        'connection fail: status: 0x{:02x}'.format(evt.status))
                self.conn_handle = evt.conn_handle
                self.log.info('connect to %s', ba2str(evt.peer_addr))
                # helper.set_data_len(self.conn_handle, 251)
                # helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)
                self.wait()

                data = self.create_test_acl_data()
                for d in data:
                    self.send_acl_data(d)

                self.wait()

                try:
                    helper.disconnect(self.conn_handle, 0x13)
                    helper.wait_disconnection_complete(self.conn_handle)
                finally:
                    helper.remove_device_from_white_list(0, peer_addr)
                succeeded = True
            except (HCICommandError, TestError):
                self.log.warning(
                    'fail to create connection by white list', exc_info=True)
                succeeded = False
            self.send(succeeded)


class LESlave(HCIWorker):
    def main(self):
        helper = LEHelper(self.sock)
        helper.reset()

        while True:
            going = self.recv()
            if not going:
                break

            try:
                helper.start_advertising(0xA0)
                evt = helper.wait_connection_complete()
                if evt.status != 0:
                    raise TestError(
                        'connection fail: status: 0x{:02x}'.format(evt.status))
                self.conn_handle = evt.conn_handle
                self.log.info('connect to %s', ba2str(evt.peer_addr))

                # helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)

                self.signal()  # trigger master to send data

                i = 0
                recv_bytes = 0
                while recv_bytes < NUM_ACL_DATA * HCI_ACL_MAX_SIZE:
                    pkt_type, pkt = self.recv_hci_pkt()
                    if pkt_type == bluez.HCI_ACLDATA_PKT:
                        recv_bytes += len(pkt.data)
                        print i, recv_bytes, pkt
                        i = i + 1
                    else:
                        self.log.info('ptype: {}, {}'.format(pkt_type, pkt))

                self.signal()  # triger master to disconnect

                helper.wait_disconnection_complete(
                    self.conn_handle, CONN_TIMEOUT_MS)
                succeeded = True
            except (HCICommandError, HCITimeoutError):
                self.log.warning('fail to connect to initiator', exc_info=True)
                succeeded = False
            self.send(succeeded)


class LETester(HCICoordinator):
    def main(self):
        print 'master[{}], slave[{}]'.format(
            ba2str(self.master.bd_addr),
            ba2str(self.slave.bd_addr))

        self.master.send(self.slave.bd_addr)

        n_run = 1
        n_case1_success = 0
        for i in xrange(1, n_run+1):
            # Start test
            self.master.send(True)
            self.slave.send(True)

            self.slave.wait()
            self.master.signal()

            self.slave.wait()
            self.master.signal()

            print 'run #{}: case 1: '.format(i),
            master_succeeded = self.master.recv()
            slave_succeeded = self.slave.recv()
            if master_succeeded and slave_succeeded:
                n_case1_success += 1
                print 'pass'
            else:
                print 'fail'

        # Stop test
        self.master.send(False)
        self.slave.send(False)

        print 'case 1 #success: {}/{}'.format(n_case1_success, n_run)


bluetest = {
    'coordinator': LETester,
    'worker': [
        ('master', LEMaster),
        ('slave', LESlave)
    ]
}


if __name__ == "__main__":
    bluetool.log_to_stream()
    bluetool.log_set_level(logging.WARNING)
    bluetool.run_config(bluetest, [1, 0])
