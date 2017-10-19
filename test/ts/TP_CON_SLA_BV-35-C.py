# TP/CON/SLA/BV-35-C [Slave Data Length Update - minimum Transmit Data Channel
# PDU length and time]
#
# Verify that the IUT as Slave correctly handles reception of an LL_LENGTH_REQ
# PDU when supporting the minimum allowed values for Transmit Data Channel PDU
# length and time

import bluetool
from bluetool.core import HCIDataTransCoordinator, HCIDataTransWorker, LEHelper
import bluetool.bluez as bluez
import bluetool.command as btcmd
import bluetool.event as btevt
import bluetool.error as bterr
from bluetool.utils import bytes2str, htole16

CONN_TIMEOUT_MS = 10000


class HCIVendorWriteLocalMaxRxOctets(btcmd.HCIVendorCommand,
                                     btcmd.CmdCompltEvtParamUnpacker):
    ocf = 0x85

    def __init__(self, local_max_rx_octets):
        super(HCIVendorWriteLocalMaxRxOctets, self).__init__()
        self.local_max_rx_octets = local_max_rx_octets

    def pack_param(self):
        return ''.join((htole16(self.local_max_rx_octets)))

btevt.register_cmd_complt_evt(HCIVendorWriteLocalMaxRxOctets)


class IUT(HCIDataTransWorker):
    def main(self):
        helper = LEHelper(self.sock)

        helper.reset()
        cmd = btcmd.HCILEWriteSuggestedDefaultDataLength(100, (100+14)*8)
        helper.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        helper.start_advertising(0xA0)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise bterr.TestError(
                'connection fail: status: 0x{:02x}'.format(evt.status))
        self.log.info('connect to %s', bytes2str(evt.peer_addr))
        conn_handle = evt.conn_handle
        helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)

        self.send(conn_handle)

        helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)
        self.wait()  # Wait lower tester to finish data length update

        self.test_acl_trans_send(CONN_TIMEOUT_MS / 1000)

        helper.disconnect(conn_handle, 0x13)
        helper.wait_disconnection_complete(conn_handle)


class LowerTester(HCIDataTransWorker):
    def main(self):
        peer_addr = self.recv()

        helper = LEHelper(self.sock)

        helper.reset()
        cmd = HCIVendorWriteLocalMaxRxOctets(100)
        helper.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        helper.create_connection_by_peer_addr(0, peer_addr, 60, 0, 200, 50)
        evt = helper.wait_connection_complete()
        if evt.status != 0:
            raise bterr.TestError(
                'connection fail: status: 0x{:02x}'.format(evt.status))
        self.log.info('connect to %s', bytes2str(evt.peer_addr))
        conn_handle = evt.conn_handle
        helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)

        self.send(conn_handle)

        helper.set_data_len(conn_handle, 251)
        helper.wait_le_event(bluez.EVT_LE_DATA_LEN_CHANGE)
        self.signal()  # Trigger next step

        self.test_acl_trans_recv(CONN_TIMEOUT_MS / 1000)

        helper.wait_disconnection_complete(conn_handle, CONN_TIMEOUT_MS)


class TestManager(HCIDataTransCoordinator):
    def main(self):
        self.lt.send(self.iut.bd_addr)

        send_conn_handle = self.iut.recv()
        recv_conn_handle = self.lt.recv()

        # Wait lower tester data length update
        self.lt.wait()
        self.iut.signal()

        acl_list = self.create_test_acl_data(send_conn_handle, 1, 251)
        succeeded = self.test_acl_trans(self.iut, self.lt, recv_conn_handle,
                                        acl_list, CONN_TIMEOUT_MS / 1000)

        if succeeded:
            return 0
        return 1


bluetest = {
    'coordinator': TestManager,
    'worker': [
        ('iut', IUT),
        ('lt', LowerTester)
    ]
}


if __name__ == "__main__":
    bluetool.log_to_stream()
    bluetool.run_config(bluetest, [0, 1])
