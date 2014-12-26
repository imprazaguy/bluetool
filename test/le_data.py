# Test white list add/remove
import time

import bluetool
from bluetool.core import HCICoordinator, HCIFilter, HCIWorker, HCIWorkerProxy, HCITask, LEHelper
from bluetool.bluez import ba2str
from bluetool.error import HCICommandError, TestError, HCITimeoutError
import bluetool.bluez as bluez
import bluetool.command as btcmd
import bluetool.event as btevt
from bluetool.data import HCIACLData

CONN_TIMEOUT_MS = 10000
HCI_ACL_MAX_SIZE = 27
NUM_ACL_DATA = 8

class LEMaster(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LEMaster, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

    def create_test_acl_data(self):
        data = [None]*NUM_ACL_DATA
        data_i = 0
        for i in xrange(0, NUM_ACL_DATA):
            if i % 8 == 0:
                pb_flag = 0x1
            else:
                pb_flag = 0x0
            data[i] = HCIACLData(self.conn_handle, pb_flag, 0x0,
                    ''.join(chr(c & 0xff) for c in xrange(data_i, data_i + HCI_ACL_MAX_SIZE)))
            data_i = (data_i + 1) % 256
        return data
        
    def main(self):
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT).all_events())
        helper = LEHelper(self.sock)

        try:
            helper.reset()
        except HCICommandError as err:
            self.log.warning('cannot reset', exc_info=True)
            return

        while True:
            going = self.recv()
            if not going:
                break

            try:
                helper.add_device_to_white_list(0, self.peer_addr)
                helper.create_connection_by_white_list(6, 0, 200, 11)
                evt = helper.wait_connection_complete()
                if evt.status != 0:
                    raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
                self.conn_handle = evt.conn_handle
                self.log.info('connect to %s', ba2str(evt.peer_addr))
                helper.set_data_len(self.conn_handle, 251)
                helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)
                self.wait()

                data = self.create_test_acl_data()
                for d in data:
                    self.send_acl_data(d)

                self.wait()

                try:
                    helper.disconnect(self.conn_handle, 0x13)
                    helper.wait_disconnection_complete(self.conn_handle)
                finally:
                    helper.remove_device_from_white_list(0, self.peer_addr)
                succeeded = True
            except (HCICommandError, TestError):
                self.log.warning('fail to create connection by white list', exc_info=True)
                succeeded = False
            self.send(succeeded)

class LESlave(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LESlave, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

    def main(self):
        self.set_hci_filter(HCIFilter(ptypes=[bluez.HCI_EVENT_PKT,bluez.HCI_ACLDATA_PKT]).all_events())
        helper = LEHelper(self.sock)

        try:
            helper.reset()
        except HCICommandError:
            self.log.warning('cannot reset', exc_info=True)
            return

        while True:
            going = self.recv()
            if not going:
                break

            try:
                helper.start_advertising(0xA0)
                evt = helper.wait_connection_complete()
                self.log.info('wait le conn complt')
                if evt.status != 0:
                    raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
                self.conn_handle = evt.conn_handle
                self.log.info('connect to %s', ba2str(evt.peer_addr))

                self.log.info('wait data len change')
                helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)

                self.send(True) # trigger master to send data

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

                self.send(True) # triger master to disconnect

                helper.wait_disconnection_complete(self.conn_handle, CONN_TIMEOUT_MS)
                succeeded = True
            except (HCICommandError, HCITimeoutError):
                self.log.warning('fail to connect to initiator', exc_info=True)
                succeeded = False
            self.send(succeeded)

class LETester(HCICoordinator):
    def __init__(self):
        super(LETester, self).__init__()
        self.worker.append(HCIWorkerProxy(0, self, LEMaster))
        self.worker.append(HCIWorkerProxy(1, self, LESlave))
        self.worker[0].worker.peer_addr = self.worker[1].bd_addr
        self.worker[1].worker.peer_addr = self.worker[0].bd_addr

    def main(self):
        print 'master[{}], slave[{}]'.format(ba2str(self.worker[0].bd_addr), ba2str(self.worker[1].bd_addr))
        
        n_run = 1
        n_case1_success = 0
        for i in xrange(1, n_run+1):
            # Start test
            self.worker[0].send(True)
            self.worker[1].send(True)

            self.worker[1].recv()
            self.worker[0].signal()

            self.worker[1].recv()
            self.worker[0].signal()

            print 'run #{}: case 1: '.format(i),
            master_succeeded = self.worker[0].recv()
            slave_succeeded = self.worker[1].recv()
            if master_succeeded and slave_succeeded:
                n_case1_success += 1
                print 'pass'
            else:
                print 'fail'

            self.worker[0].signal()
            self.worker[1].signal()

        # Stop test
        self.worker[0].send(False) 
        self.worker[1].send(False)

        print 'case 1 #success: {}/{}'.format(n_case1_success, n_run)


if __name__ == "__main__":
    bluetool.log_to_stream()
    tester = LETester()
    tester.run()

