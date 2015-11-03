"""Core module for HCI operations.
"""
import logging
import multiprocessing as mp
import os
import select
import signal

from . import bluez
from . import command as btcmd
from . import event as btevt
from .command import HCICommand, HCIReadBDAddr
from .data import HCIACLData, HCISCOData
from .error import HCICommandError, HCIParseError, HCITimeoutError
from .event import HCIEvent
from .utils import letoh8


_pkt_table = {
        bluez.HCI_COMMAND_PKT: HCICommand,
        bluez.HCI_ACLDATA_PKT: HCIACLData,
        bluez.HCI_SCODATA_PKT: HCISCOData,
        bluez.HCI_EVENT_PKT: HCIEvent,
}

def get_hci_pkt_size(buf, offset=0):
    ptype = letoh8(buf, offset)
    offset += 1
    return 1 + _pkt_table[ptype].get_pkt_size(buf, offset)

def parse_hci_pkt(buf, offset=0):
    ptype = letoh8(buf, offset)
    offset += 1
    pkt = _pkt_table[ptype].parse(buf, offset)
    return (ptype, pkt)

class HCISock(object):
    def __init__(self, dev_id):
        super(HCISock, self).__init__()
        self.sock = bluez.hci_new_user_channel(dev_id)
        self.poll = select.poll()
        self.poll.register(self.sock, (select.POLLIN | select.POLLPRI))
        self.rbuf = ''

    def __del__(self):
        self.poll.unregister(self.sock)
        self.sock.close()
    
    def fileno(self):
        return self.sock.fileno()

    def send_hci_cmd(self, cmd):
        param = cmd.pack_param()
        if param is not None:
            bluez.hci_send_cmd(self.sock, cmd.ogf, cmd.ocf, param)
        else:
            bluez.hci_send_cmd(self.sock, cmd.ogf, cmd.ocf)

    def send_acl_data(self, acl):
        bluez.hci_send_acl(self.sock, acl.conn_handle, acl.pb_flag,
                acl.bc_flag, acl.data)

    def recv_hci_pkt(self, timeout=None):
        """Receive a HCI packet.

        This method waits for timeout milliseconds to receive a packet. If the
        time is out, it raises HCITimeoutError exception. timeout is ignored
        if timeout is None.
        """
        while True:
            if len(self.rbuf) > 0:
                pkt_size = get_hci_pkt_size(self.rbuf)
                if pkt_size <= len(self.rbuf):
                    break
            if timeout is not None:
                if len(self.poll.poll(timeout)) == 0:
                    raise HCITimeoutError
            buf = self.sock.recv(1024)
            self.rbuf = ''.join((self.rbuf, buf))

        ptype_pkt = parse_hci_pkt(self.rbuf)
        self.rbuf = self.rbuf[pkt_size:]
        return ptype_pkt

    def recv_hci_evt(self, timeout=None):
        ptype, evt = self.recv_hci_pkt(timeout)
        if ptype != bluez.HCI_EVENT_PKT:
            raise HCIParseError('not an event: ptype: {}'.format(ptype))
        return evt

class HCITask(object):
    def __init__(self, hci_sock):
        super(HCITask, self).__init__()
        self.sock = hci_sock
        self.log = logging.getLogger('{}.{}'.format(__name__, HCITask))

    def send_hci_cmd(self, cmd):
        self.sock.send_hci_cmd(cmd)

    def send_acl_data(self, data):
        self.sock.send_acl_data(data)

    def recv_hci_pkt(self, timeout=None):
        return self.sock.recv_hci_pkt(timeout)

    def recv_hci_evt(self, timeout=None):
        return self.sock.recv_hci_evt(timeout)

    def wait_hci_evt(self, evt_matcher, timeout=None):
        while True:
            evt = self.recv_hci_evt(timeout)
            if evt_matcher(evt):
                #self.log.info('wait evt: 0x{:02x}'.format(evt.code))
                return evt
            self.log.info('ignore event: 0x{:02x}'.format(evt.code))

    def send_hci_cmd_wait_cmd_complt(self, cmd):
        self.send_hci_cmd(cmd)
        evt = self.wait_hci_evt(lambda evt: evt.code == bluez.EVT_CMD_COMPLETE and evt.cmd_opcode == cmd.opcode())
        return evt

    def send_hci_cmd_wait_cmd_status(self, cmd):
        self.send_hci_cmd(cmd)
        evt = self.wait_hci_evt(lambda evt: evt.code == bluez.EVT_CMD_STATUS and evt.cmd_opcode == cmd.opcode())
        return evt

class HCIWorker(HCITask, mp.Process):
    def __init__(self, hci_sock, coord, pipe):
        super(HCIWorker, self).__init__(hci_sock)
        self.coord = coord
        self.pipe = pipe
        self.event = mp.Event()
        self.log = logging.getLogger('{}.HCIWorker'.format(__name__))

    def run(self):
        try:
            self.main()
        except Exception:
            self.coord.put_terminated_worker(self.pid)
            os.kill(self.coord.pid, signal.SIGINT)
            raise

    def main(self):
        """Main function of worker object.
        
        Subclass should implement this method to provide main function.
        """
        raise NotImplementedError

    def wait(self):
        self.event.wait()
        self.event.clear()

    def signal(self):
        self.event.set()

    def send(self, obj):
        self.pipe.send(obj)

    def recv(self):
        return self.pipe.recv()

class ReadBDAddrTask(HCITask):
    def __init__(self, hci_sock):
        super(ReadBDAddrTask, self).__init__(hci_sock)

    def read_bd_addr(self):
        cmd = HCIReadBDAddr()
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        return evt.bd_addr

class HCIWorkerProxy(object):
    def __init__(self, dev_id, coord, worker_type, *args):
        self.sock = HCISock(dev_id)
        self.bd_addr = ReadBDAddrTask(self.sock).read_bd_addr()
        self.pipe, pipe = mp.Pipe()
        self.worker = worker_type(self.sock, coord, pipe, *args)

    @property
    def pid(self):
        return self.worker.pid

    def signal(self):
        self.worker.signal()

    def send(self, obj):
        self.pipe.send(obj)

    def recv(self):
        return self.pipe.recv()

    def start(self):
        self.worker.start()

    def join(self):
        self.worker.join()

    def terminate(self):
        self.worker.terminate()

class HCICoordinator(object):
    def __init__(self):
        super(HCICoordinator, self).__init__()
        self.worker = []
        self.pid = os.getpid()
        self.term_worker_queue = mp.Queue()
        self.log = logging.getLogger('{}.{}'.format(__name__, self.__class__.__name__))

    def run(self):
        for w in self.worker:
            w.start()
        try:
            self.main()
        except KeyboardInterrupt:
            term_workers = self.get_terminated_workers()
            for w in self.worker:
                if w.pid not in term_workers:
                    w.terminate()
        for w in self.worker:
            w.join()

    def get_terminated_workers(self):
        """Get pids of terminated workers."""
        workers = set()
        workers.add(self.term_worker_queue.get())
        # Just make sure get one pid of terminated workers. If more than
        # one pid are put into queue, we don't care missing them.
        while not self.term_worker_queue.empty():
            workers.add(self.term_worker_queue.get_nowait())
        return workers

    def put_terminated_worker(self, pid):
        self.term_worker_queue.put(pid)

    def main(self):
        """Main function of coordinator object.
        
        Subclass should implement this method to provide main function.
        """
        raise NotImplementedError

class BTHelper(HCITask):
    def __init__(self, hci_sock):
        super(BTHelper, self).__init__(hci_sock)

    def check_hci_evt_status(self, evt):
        if evt.status != 0:
            raise HCICommandError(evt)

    def send_hci_cmd_wait_cmd_complt_check_status(self, cmd):
        evt = self.send_hci_cmd_wait_cmd_complt(cmd)
        self.check_hci_evt_status(evt)
        return evt

    def send_hci_cmd_wait_cmd_status_check_status(self, cmd):
        evt = self.send_hci_cmd_wait_cmd_status(cmd)
        self.check_hci_evt_status(evt)
        return evt

class BREDRHelper(BTHelper):
    def __init__(self, hci_sock):
        super(BREDRHelper, self).__init__(hci_sock)

    def reset(self):
        cmd = btcmd.HCIReset()
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        cmd = btcmd.HCISetEventMask(0x20001FFFFFFFFFFFL)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        cmd = btcmd.HCIWritePageScanActivity(0x0800, 0x0012)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        cmd = btcmd.HCIWriteScanEnable(0x02)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def create_connection_by_peer_addr(self, peer_addr):
        cmd = btcmd.HCICreateConnection(peer_addr, 0x0000, 0x01, 0x0000, 0x00)
        self.send_hci_cmd_wait_cmd_status_check_status(cmd)

    def accept_connection(self, timeout=None):
        evt = self.wait_hci_evt(lambda evt: evt.code == bluez.EVT_CONN_REQUEST, timeout)
        cmd = btcmd.HCIAcceptConnectionRequest(evt.bd_addr, 0x01)
        self.send_hci_cmd_wait_cmd_status_check_status(cmd)

    def wait_connection_complete(self, timeout=None):
        return self.wait_hci_evt(
                lambda evt: evt.code == bluez.EVT_CONN_COMPLETE,
                timeout)

    def wait_disconnection_complete(self, conn_handle=None, timeout=None):
        return self.wait_hci_evt(
                lambda evt: evt.code == bluez.EVT_DISCONN_COMPLETE and (conn_handle is None or conn_handle == evt.conn_handle),
                timeout)

class LEHelper(BTHelper):
    def __init__(self, hci_sock):
        super(LEHelper, self).__init__(hci_sock)
        self.init_scan_intvl = 96
        self.init_scan_win = 24

    def reset(self):
        cmd = btcmd.HCIReset()
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        cmd = btcmd.HCISetEventMask(0x20001FFFFFFFFFFFL)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        cmd = btcmd.HCILESetEventMask(0x7ff)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        cmd = btcmd.HCILEClearWhiteList()
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def read_buffer_size(self):
        cmd = btcmd.HCILEReadBufferSize()
        return self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def add_device_to_white_list(self, peer_addr_type, peer_addr):
        cmd = btcmd.HCILEAddDeviceToWhiteList(peer_addr_type, peer_addr)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def remove_device_from_white_list(self, peer_addr_type, peer_addr):
        cmd = btcmd.HCILERemoveDeviceFromWhiteList(peer_addr_type, peer_addr)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def create_connection_by_peer_addr(self, peer_addr_type, peer_addr, conn_intvl, conn_latency, supv_to, ce_len):
        cmd = btcmd.HCILECreateConnection(self.init_scan_intvl,
                self.init_scan_win, 0, peer_addr_type, peer_addr, 0,
                conn_intvl, conn_intvl, conn_latency, supv_to, ce_len, ce_len)
        self.send_hci_cmd_wait_cmd_status_check_status(cmd)

    def create_connection_by_white_list(self, conn_intvl, conn_latency, supv_to, ce_len):
        cmd = btcmd.HCILECreateConnection(self.init_scan_intvl,
                self.init_scan_win, 1, 0, '\x00'*6, 0, conn_intvl, conn_intvl,
                conn_latency, supv_to, ce_len, ce_len)
        self.send_hci_cmd_wait_cmd_status_check_status(cmd)

    def create_connect_cancel(self):
        cmd = btcmd.HCILECreateConnectionCancel()
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def connection_update(self, conn_handle, conn_intvl, conn_latency,
            supv_timeout, ce_len):
        cmd = btcmd.HCILEConnectionUpdate(conn_handle, conn_intvl, conn_intvl,
                conn_latency, supv_timeout, ce_len, ce_len)
        self.send_hci_cmd_wait_cmd_status_check_status(cmd)

    def set_host_classification(self, channel_map):
        cmd = btcmd.HCILESetHostChannelClassification(channel_map)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def disconnect(self, conn_handle, reason):
        cmd = btcmd.HCIDisconnect(conn_handle, reason)
        self.send_hci_cmd_wait_cmd_status_check_status(cmd)

    def set_advertising_data(self, data):
        cmd = btcmd.HCILESetAdvertisingData(data)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def start_advertising(self, intvl):
        cmd = btcmd.HCILESetAdvertisingParameters(intvl, intvl, 0, 0, 0, '\x00'*6, 0x7, 0)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

        cmd = btcmd.HCILESetAdvertiseEnable(1)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def stop_advertising(self):
        cmd = btcmd.HCILESetAdvertiseEnable(0)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

    def wait_le_event(self, subevt_code, timeout=None):
        return self.wait_hci_evt(
                lambda evt: evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == subevt_code,
                timeout)

    def wait_connection_complete(self, timeout=None):
        return self.wait_hci_evt(
                lambda evt: evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == bluez.EVT_LE_CONN_COMPLETE,
                timeout)

    def wait_connection_update_complete(self, timeout=None):
        return self.wait_hci_evt(
                lambda evt: evt.code == bluez.EVT_LE_META_EVENT and evt.subevt_code == bluez.EVT_LE_CONN_UPDATE_COMPLETE,
                timeout)

    def wait_disconnection_complete(self, conn_handle=None, timeout=None):
        return self.wait_hci_evt(
                lambda evt: evt.code == bluez.EVT_DISCONN_COMPLETE and (conn_handle is None or conn_handle == evt.conn_handle),
                timeout)

    def set_data_len(self, conn_handle, tx_octets):
        # 14 = 1(Preamble) + 4(Access Code) + 2(PDU Header) + 4(MIC) + 3(CRC)
        tx_time = (tx_octets + 14) * 8
        cmd = btcmd.HCILESetDataLength(conn_handle, tx_octets, tx_time)
        self.send_hci_cmd_wait_cmd_complt_check_status(cmd)

