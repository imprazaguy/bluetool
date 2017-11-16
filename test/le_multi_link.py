# Test LE multiple link QoS

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, LEHelper, ReadBDAddrTask
from bluetool.error import HCICommandError, TestError, HCITimeoutError
from bluetool.utils import bytes2str
from bluetool import bluez
import logging
import time


class LEMaster(HCIWorker):
    def main(self):
        self.num_peers = self.recv()
        self.peer_addr = self.recv()
        self.conn_handle = [0]*self.num_peers
        self.connected = [False]*self.num_peers

        helper = LEHelper(self.sock)
        helper.reset()

        self.signal()  # signal master reset completion

        while True:
            going = self.recv()
            if not going:
                break

            try:
                i = 0
                while i < self.num_peers:
                    helper.create_connection_by_peer_addr(
                        0, self.peer_addr[i], 12, 0, 1000, 6)
                    self.log.info('create connection to %s',
                                  bytes2str(self.peer_addr[i]))
                    evt = helper.wait_connection_complete()
                    if evt.status != 0:
                        raise TestError(
                            'connection fail: status: 0x{:02x}'.format(
                                evt.status))
                    self.conn_handle[i] = evt.conn_handle
                    self.connected[i] = True
                    self.log.info('connect to %s', bytes2str(evt.peer_addr))
                    try:
                        self.wait(10)  # wait slave connection complete
                    except HCITimeoutError:
                        evt = helper.wait_disconnection_complete(
                            self.conn_handle[i])
                        if evt.reason == 0x3E:
                            continue
                        raise TestError(
                            'disconnect {} reason 0x{:02x}'.format(
                                bytes2str(self.peer_addr[i]), evt.reason))

                    time.sleep(0.1)
                    i += 1

                last_i = self.num_peers - 1
                for ce_interval in xrange(13, 37):
                    helper.connection_update(
                        self.conn_handle[last_i], ce_interval, 0, 1000, 6)
                    while True:
                        evt = self.recv_hci_evt(10000)
                        if (evt.code == bluez.EVT_LE_META_EVENT
                                and (evt.subevt_code
                                     == bluez.EVT_LE_CONN_UPDATE_COMPLETE)):
                            if evt.status == 0:
                                break
                            else:
                                raise TestError(
                                    ('connection update with {} failed: '
                                     'status 0x{:02x}').format(
                                        bytes2str(self.peer_addr[last_i]),
                                        evt.status))
                        elif evt.code == bluez.EVT_DISCONN_COMPLETE:
                            self.connected[last_i] = False
                            raise TestError(
                                'disconnect {} reason 0x{:02x}'.format(
                                    bytes2str(self.peer_addr[last_i]),
                                    evt.reason))
                    # Make sure no supervision timeout in 10 secs
                    try:
                        evt = helper.wait_disconnection_complete(None, 10000)
                        self.connected[last_i] = False
                        raise TestError(
                            'disconnect handle 0x{:x} reason 0x{:02x}'.format(
                                evt.conn_handle, evt.reason))
                    except HCITimeoutError:
                        pass

                for i in xrange(0, self.num_peers):
                    helper.disconnect(self.conn_handle[i], 0x13)
                    helper.wait_disconnection_complete(self.conn_handle[i])
                    self.connected[i] = False

                succeeded = True
            except (HCICommandError, HCITimeoutError, TestError) as err:
                for i in xrange(0, self.num_peers):
                    if self.connected[i]:
                        helper.disconnect(self.conn_handle[i], 0x13)
                        helper.wait_disconnection_complete(self.conn_handle[i])
                        self.connected[i] = False
                self.log.warning(str(err), exc_info=True)
                succeeded = False
            self.send(succeeded)


class LESlave(HCIWorker):
    def main(self):
        self.wait()

        helper = LEHelper(self.sock)
        helper.reset()

        local_bd_addr = ReadBDAddrTask(self.sock).read_bd_addr()
        self.log.info('%s running...', bytes2str(local_bd_addr))

        self.send(True)

        while True:
            self.log.info('%s wait...', bytes2str(local_bd_addr))
            going = self.recv()
            if not going:
                break

            try:
                helper.start_advertising(0xA0)
                self.log.info('%s starts advertising',
                              bytes2str(local_bd_addr))
                evt = helper.wait_connection_complete()
                if evt.status != 0:
                    raise TestError(
                        'connection fail: status: 0x{:02x}'.format(evt.status))
                self.conn_handle = evt.conn_handle
                self.log.info('connect to %s', bytes2str(evt.peer_addr))

                self.signal()  # tell master of connection complete

                helper.wait_disconnection_complete(self.conn_handle)
                succeeded = True
            except (HCICommandError, HCITimeoutError) as err:
                self.log.warning(str(err), exc_info=True)
                succeeded = False
            self.send(succeeded)


class LETester(HCICoordinator):
    def main(self):
        self.log.info('master[%s]', bytes2str(self.master.bd_addr))
        slave = [
            self.slave1,
            self.slave2,
            self.slave3,
            self.slave4
        ]
        for i, s in enumerate(slave):
            self.log.info('slave%d[%s]', i + 1, bytes2str(s.bd_addr))

        self.master.send(len(slave))
        self.master.send([s.bd_addr for s in slave])
        self.master.wait()

        for s in slave:
            s.signal()  # wake slave to do initialization
            s.recv()  # wait for slave to complete initialization

        n_run = 10
        n_case1_success = 0
        for i in xrange(1, n_run+1):
            # Start test
            self.master.send(True)

            for s in slave:
                s.send(True)
                self.log.info('tester sends true to %s', bytes2str(s.bd_addr))
                s.wait()
                self.log.info('tester receives from %s', bytes2str(s.bd_addr))
                self.master.signal()

            print 'run #{}: '.format(i),
            succeeded = self.master.recv()
            for s in slave:
                succeeded = succeeded and s.recv()
            if succeeded:
                n_case1_success += 1
                print 'pass'
            else:
                print 'fail'

        # Stop test
        self.master.send(False)
        for s in slave:
            s.send(False)

        print '#success: {}/{}'.format(n_case1_success, n_run)


bluetest = {
    'coordinator': LETester,
    'worker': [
        ('master', LEMaster),
        ('slave1', LESlave),
        ('slave2', LESlave),
        ('slave3', LESlave),
        ('slave4', LESlave)
    ]
}


if __name__ == "__main__":
    bluetool.log_to_stream()
    bluetool.log_set_level(logging.INFO)
    bluetool.run_config(bluetest, [4, 0, 1, 2, 3])
