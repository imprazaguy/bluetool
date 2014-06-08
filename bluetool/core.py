"""Core module for HCI operations.
"""
import logging
import multiprocessing as mp
import os
import select
import signal

from . import bluez
from .command import HCICommand, HCIReadBDAddr
from .data import HCIACLData, HCISCOData
from .error import HCIParseError, HCITimeoutError
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

class HCIFilter(object):
    def __init__(self, obj=None, ptypes=None, events=None, opcode=None):
        super(HCIFilter, self).__init__()
        if obj is None:
            self.obj = bluez.hci_filter_new()
        else:
            self.obj = obj
        if ptypes is not None:
            try:
                self.ptype(*ptypes)
            except TypeError:
                self.ptype(ptypes)
        if events is not None:
            try:
                self.event(*events)
            except TypeError:
                self.event(events)
        if opcode is not None:
            self.opcode(opcode)

    def ptype(self, *args):
        for pt in args:
            bluez.hci_filter_set_ptype(self.obj, pt)
        return self

    def event(self, *args):
        for evt in args:
            bluez.hci_filter_set_event(self.obj, evt)
        return self

    def all_events(self):
        bluez.hci_filter_all_events(self.obj)
        return self

    def opcode(self, opcode):
        bluez.hci_filter_set_opcode(self.obj, opcode)
        return self

class HCISock(object):
    def __init__(self, dev_id):
        super(HCISock, self).__init__()
        self.sock = bluez.hci_open_dev(dev_id)
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

    def get_hci_filter(self):
        return HCIFilter(self.sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14))

    def set_hci_filter(self, flt):
        self.sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt.obj)

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

        pkt = parse_hci_pkt(self.rbuf)
        self.rbuf = self.rbuf[pkt_size:]
        return pkt

    def recv_hci_evt(self, timeout=None):
        ptype, evt = self.recv_hci_pkt(timeout)
        if ptype != bluez.HCI_EVENT_PKT:
            raise HCIParseError('not an event: ptype: {})'.format(ptype))
        return evt

class HCITask(object):
    def __init__(self, hci_sock):
        super(HCITask, self).__init__()
        self.sock = hci_sock

    def send_hci_cmd(self, cmd):
        self.sock.send_hci_cmd(cmd)

    def get_hci_filter(self):
        return self.sock.get_hci_filter()

    def set_hci_filter(self, flt):
        self.sock.set_hci_filter(flt)

    def recv_hci_pkt(self, timeout=None):
        return self.scok.recv_hci_pkt(timeout)

    def recv_hci_evt(self, timeout=None):
        return self.sock.recv_hci_evt(timeout)

    def send_hci_cmd_wait_cmd_complt(self, cmd):
        old_flt = self.get_hci_filter()
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT,
            events=bluez.EVT_CMD_COMPLETE, opcode=cmd.opcode))
        self.send_hci_cmd(cmd)
        while True:
            evt = self.recv_hci_evt()
            if evt.code == bluez.EVT_CMD_COMPLETE:
                break
        self.set_hci_filter(old_flt)
        return evt

    def send_hci_cmd_wait_cmd_status(self, cmd):
        old_flt = self.get_hci_filter()
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT,
            events=bluez.EVT_CMD_STATUS))
        self.send_hci_cmd(cmd)
        while True:
            evt = self.recv_hci_evt()
            if evt.code == bluez.EVT_CMD_STATUS:
                break
        self.set_hci_filter(old_flt)
        return evt

_logger = mp.log_to_stderr()
_logger.setLevel(logging.INFO)

class HCIWorker(HCITask, mp.Process):
    log = _logger

    def __init__(self, hci_sock, coord, pipe):
        super(HCIWorker, self).__init__(hci_sock)
        self.coord = coord
        self.pipe = pipe
        self.event = mp.Event()

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

