# Test host and remote device disconnect simultaneously and quickly create
# connection again.
import time

from bluetool.core import HCICoordinator, HCIFilter, HCIWorker, HCIWorkerProxy, HCITask
from bluetool.bluez import ba2str
from bluetool.error import HCICommandError, TestError
import bluetool.bluez as bluez
import bluetool.command as btcmd
import bluetool.event as btevt

class LEHelper(HCITask):
    def __init__(self, hci_sock):
        super(LEHelper, self).__init__(hci_sock)

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

    def add_device_to_white_list(self, peer_addr_type, peer_addr):
        cmd = btcmd.HCILEAddDeviceToWhiteList(peer_addr_type, peer_addr)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def remove_device_from_white_list(self, peer_addr_type, peer_addr):
        cmd = btcmd.HCILERemoveDeviceFromWhiteList(peer_addr_type, peer_addr)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def create_connect_by_white_list(self, conn_intvl, timeout):
        cmd = btcmd.HCILECreateConnection(96, 24, 1, 0, '\x00'*6, 0, conn_intvl, conn_intvl, 0, 100, 0, 0)
        evt = self.send_hci_cmd_wait_cmd_status(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def create_connect_cancel(self):
        cmd = btcmd.HCILECreateConnectionCancel()
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def disconnect(self, conn_handle, reason):
        cmd = btcmd.HCIDisconnect(conn_handle, reason)
        evt = self.send_hci_cmd_wait_cmd_status(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def start_advertising(self):
        cmd = btcmd.HCILESetAdvertisingParameters(0xA0, 0xA0, 0, 0, 0, '\x00'*6, 0x7, 0)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

        cmd = btcmd.HCILESetAdvertiseEnable(1)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def stop_advertising(self):
        cmd = btcmd.HCILESetAdvertiseEnable(0)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        if evt.status != 0:
            raise HCICommandError(evt)

    def wait_connection_complete(self):
        while True:
            evt = self.recv_hci_evt()
            if evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE:
                return evt
            else:
                self.log.info('ignore event: %d', evt.code)

    def wait_disconnection_complete(self):
        while True:
            evt = self.recv_hci_evt()
            if evt.code == bluez.EVT_DISCONN_COMPLETE:
                return evt
            else:
                self.log.info('ignore event: %d', evt.code)


class LEInitiator(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LEInitiator, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

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
                helper.create_connect_by_white_list(80, None)
                evt = helper.wait_connection_complete()
                if evt.status != 0:
                    raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
                self.conn_handle = evt.conn_handle
                succeeded = True
            except (HCICommandError, TestError):
                self.log.warning('fail to create connection', exc_info=True)
                succeeded = False
            # inform coordinator of connection complete
            self.send(succeeded)
            # check if advertiser gets connection complete and synchronize with
            # advertiser
            succeeded = self.recv()
            if not succeeded:
                continue

            time.sleep(0.1)
            try:
                helper.disconnect(self.conn_handle, 0x13)
                helper.create_connect_by_white_list(80, None)

                while True:
                    evt = self.recv_hci_evt()
                    if evt.code == bluez.EVT_DISCONN_COMPLETE:
                        self.log.info('disconnect complete: conn_handle: 0x{:x}'.format(evt.conn_handle))
                    elif (evt.code == bluez.EVT_LE_META_EVENT
                            and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE):
                        if evt.status != 0:
                            raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
                        self.conn_handle = evt.conn_handle
                        break
                    else:
                        self.log.info('ignore event: %d', evt.code)

                #helper.disconnect(self.conn_handle, 0x13)
                #helper.wait_disconnection_complete()
                succeeded = True
            except (HCICommandError, TestError):
                self.log.warning('fail to disconnect and connect simultaneously', exc_info=True)
                succeeded = False
            self.send(succeeded)

class LEAdvertiser(HCIWorker):
    def __init__(self, hci_sock, coord, pipe, peer_addr=None):
        super(LEAdvertiser, self).__init__(hci_sock, coord, pipe)
        self.peer_addr = peer_addr

    def main(self):
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT).all_events())
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
                helper.start_advertising()
                evt = helper.wait_connection_complete()
                helper.stop_advertising()
                if evt.status != 0:
                    raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
                self.conn_handle = evt.conn_handle
                succeeded = True
            except (HCICommandError, TestError):
                self.log.warning('fail to connect to initiator', exc_info=True)
                succeeded = False
            # inform coordinator of connection complete
            self.send(succeeded)
            # check initiator gets connection complete and synchronize with initiator
            succeeded = self.recv()
            if not succeeded:
                continue

            try:
                helper.disconnect(self.conn_handle, 0x13)
                helper.wait_disconnection_complete()
                helper.start_advertising()
                while True:
                    evt = self.recv_hci_evt()
                    if evt.code == bluez.EVT_DISCONN_COMPLETE:
                        self.log.info('disconnect complete: conn_handle: 0x{:x}'.format(evt.conn_handle))
                    elif (evt.code == bluez.EVT_LE_META_EVENT
                            and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE):
                        if evt.status != 0:
                            raise TestError('connection fail: status: 0x{:02x}'.format(evt.status))
                        self.conn_handle = evt.conn_handle
                        break
                    else:
                        self.log.info('ignore event: %d', evt.code)
                #helper.wait_disconnection_complete()
                succeeded = True
            except HCICommandError:
                self.log.warning('fail to disconnect and connect simultaneously', exc_info=True)
                succeeded = False
            self.send(succeeded)

class TwoDisconnectTester(HCICoordinator):
    def __init__(self):
        super(TwoDisconnectTester, self).__init__()
        self.worker.append(HCIWorkerProxy(0, self, LEInitiator))
        self.worker.append(HCIWorkerProxy(1, self, LEAdvertiser))
        self.worker[0].worker.peer_addr = self.worker[1].bd_addr
        self.worker[1].worker.peer_addr = self.worker[0].bd_addr

    def main(self):
        print 'master[{}], slave[{}]'.format(ba2str(self.worker[0].bd_addr), ba2str(self.worker[1].bd_addr))
        
        n_run = 1
        n_success = 0
        for i in xrange(0, n_run):
            # start test
            for w in self.worker:
                w.send(True)

            # synchronize initiator and advertiser
            init_succeeded = self.worker[0].recv()
            adv_succeeded = self.worker[1].recv()
            if not init_succeeded or not adv_succeeded:
                for w in self.worker:
                    w.send(False)
                continue
            else:
                for w in self.worker:
                    w.send(True)

            init_succeeded = self.worker[0].recv()
            adv_succeeded = self.worker[1].recv()
            if init_succeeded and adv_succeeded:
                n_success += 1

        # stop test
        for w in self.worker:
            w.send(False)

        print '#success: {}/{}'.format(n_success, n_run)


if __name__ == "__main__":
    tester = TwoDisconnectTester()
    tester.run()

