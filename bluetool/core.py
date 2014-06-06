"""Core module for HCI operations.
"""
import multiprocessing as mp

from . import bluez
from .command import HCICommand, HCIReadBDAddr
from .event import HCIEvent, parse_hci_event
from .data import HCIACLData, HCISCOData


class HCIError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

def get_hci_pkt_size(buf, offset=0):
    ptype = ord(buf[offset])
    offset += 1
    if ptype == bluez.HCI_COMMAND_PKT:
        pkt_size = HCICommand.get_pkt_size(buf, offset)
    elif ptype == bluez.HCI_ACLDATA_PKT:
        pkt_size = HCIACLData.get_pkt_size(buf, offset)
    elif ptype == bluez.HCI_SCODATA_PKT:
        pkt_size = HCISCOData.get_pkt_size(buf, offset)
    elif ptype == bluez.HCI_EVENT_PKT:
        pkt_size = HCIEvent.get_pkt_size(buf, offset)
    else:
        raise HCIError('unknown ptype: 0x{:02x}'.format(ptype))
    return pkt_size

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
        self.rbuf = ''
    
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

    def has_hci_pkt_in_buf(self):
        if len(self.rbuf) == 0:
            return False
        if get_hci_pkt_size(self.rbuf) > len(self.rbuf):
            return False
        return True

    def recv_hci_evt(self):
        while not self.has_hci_pkt_in_buf():
            buf = self.sock.recv(1024)
            self.rbuf = ''.join((self.rbuf, buf))
        ptype = ord(self.rbuf[0])
        evt_code = ord(self.rbuf[1])
        plen = ord(self.rbuf[2])
        evt = parse_hci_event(evt_code, self.rbuf, 3)
        self.rbuf = self.rbuf[3+plen:]
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

    def recv_hci_evt(self):
        return self.sock.recv_hci_evt()

    def send_hci_cmd_wait_cmd_complt(self, cmd):
        old_flt = self.get_hci_filter()
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT,
            events=bluez.EVT_CMD_COMPLETE, opcode=cmd.opcode))
        self.send_hci_cmd(cmd)
        evt = self.recv_hci_evt()
        self.set_hci_filter(old_flt)
        return evt

    def send_hci_cmd_wait_cmd_status(self, cmd):
        old_flt = self.get_hci_filter()
        self.set_hci_filter(HCIFilter(ptypes=bluez.HCI_EVENT_PKT,
            events=bluez.EVT_CMD_STATUS))
        self.send_hci_cmd(cmd)
        evt = self.recv_hci_evt()
        self.set_hci_filter(old_flt)
        return evt

class HCIWorker(HCITask, mp.Process):
    def __init__(self, hci_sock, pipe):
        super(HCIWorker, self).__init__(hci_sock)
        self.pipe = pipe
        self.event = mp.Event()

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
    def __init__(self, dev_id, worker_type, *args):
        self.sock = HCISock(dev_id)
        self.bd_addr = ReadBDAddrTask(self.sock).read_bd_addr()
        self.pipe, pipe = mp.Pipe()
        self.worker = worker_type(self.sock, pipe, *args)

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

class HCICoordinator(object):
    def __init__(self):
        super(HCICoordinator, self).__init__()

    def main(self):
        raise NotImplementedError

