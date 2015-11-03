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
from bluetool.utils import bytes2str, htole16

CONN_TIMEOUT_MS = 10000
HCI_ACL_MAX_SIZE = 251
NUM_ACL_DATA = 1600


class LEMaster(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LEMaster, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

    def main(self):
        helper = LEHelper(self.sock)

        try:
            helper.reset()
            cmd = btcmd.HCILEWriteSuggestedDefaultDataLength(251, (251+14)*8)
            helper.send_hci_cmd_wait_cmd_complt_check_status(cmd)
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
        self.wait() # Wait slave to connect and reject LL_LENGTH_REQ

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
        self.send(True) # Trigger next step

        # Receive ACL data
        keep_receive_data = True
        while keep_receive_data:
            num_acl_data = self.recv()
            if num_acl_data <= 0:
                break
            try:
                i = 0
                while i < num_acl_data:
                    pkt_type, pkt = self.recv_hci_pkt()
                    if pkt_type == bluez.HCI_ACLDATA_PKT:
                        self.send(pkt)
                        status = self.recv() # If data received are correct
                        if status == 0:
                            continue
                        if status < 0:
                            keep_receive_data = False
                            break
                        i += 1
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

    def create_test_acl_data(self, conn_handle, num_acl_data=NUM_ACL_DATA, acl_size=HCI_ACL_MAX_SIZE):
        data = [None]*num_acl_data
        data_i = 0
        for i in xrange(0, num_acl_data):
            data[i] = HCIACLData(conn_handle, 0x0, 0x0,
                    ''.join(chr(c & 0xff) for c in xrange(data_i, data_i + acl_size)))
            data_i = (data_i + 1) % 256
        return data

    def test_acl_trans(self, conn_handle, acl):
        print acl
        self.worker[0].send(acl)

        acl_recv = self.worker[1].recv()
        acl_data = acl_recv.data
        if acl_data == acl.data:
            succeeded = True
            self.worker[1].send(1)
        else:
            while True:
                self.worker[1].send(0)
                acl_recv = self.worker[1].recv()
                if acl_recv.pb_flag != 0x1:
                    succeeded = False
                    self.worker[1].send(-1)
                    break
                acl_data += acl_recv.data
                if acl_data == acl.data:
                    succeeded = True
                    self.worker[1].send(1)
                    break

        self.worker[0].send(succeeded)
        if not succeeded:
            self.log.warning("incorrect data received: {}".format(bytes2str(acl_data)))

    def main(self):
        print 'master[{}], slave[{}]'.format(ba2str(self.worker[0].bd_addr), ba2str(self.worker[1].bd_addr))

        conn_handle = self.worker[0].recv()
        # Wait connection establishment
        self.worker[1].recv()
        time.sleep(1) # Wait for data length update procedure to finish
        self.worker[0].signal()

        self.worker[0].send(1) # Number of ACL data to send
        self.worker[1].send(1) # Number of ACL data to receive
        acl = self.create_test_acl_data(conn_handle, 1, 251)
        self.test_acl_trans(conn_handle, acl[0])

        self.worker[0].send(0)
        self.worker[1].send(0)

if __name__ == "__main__":
    bluetool.log_to_stream()
    tester = LETester()
    tester.run()
