
import struct
import bluetooth._bluetooth as bluez

from .command import HCICommand
from .event import HCIEvent, parse_hci_event
from .data import HCIACLData, HCISCOData

class HCITask(object):
    def __init__(self, worker):
        self.worker = worker

    def run(self):
        """Perform actions."""
        raise NotImplementedError

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

class HCISock(object):
    def __init__(self, dev_id):
        self.sock = bluez.hci_open_dev(dev_id)
        self.rbuf = ''
    
    def send_hci_cmd(self, cmd_pkt):
        param = cmd_pkt.pack_param()
        if param is not None:
            bluez.hci_send_cmd(self.sock, cmd_pkt.ogf, cmd_pkt.ocf, param)
        else:
            bluez.hci_send_cmd(self.sock, cmd_pkt.ogf, cmd_pkt.ocf)

    def get_hci_filter(self):
        return self.sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)

    def new_hci_filter(self, ptype=None, event=None, opcode=None):
        flt = bluez.hci_filter_new()
        if ptype is None:
            bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
        else:
            for t in ptype:
                bluez.hci_filter_set_ptype(flt, t)
        if event is None:
            bluez.hci_filter_all_events(flt)
        else:
            for e in event:
                bluez.hci_filter_set_event(flt, e)
        if opcode is not None:
            bluez.hci_filter_set_opcode(flt, opcode)
        return flt

    def set_hci_filter(self, flt):
        self.sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt)

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

class HCIWorker(object):
    def __init__(self, hci_sock):
        self.sock = hci_sock

    def run(self):
        raise NotImplementedError

    def send_hci_cmd(self, cmd_pkt):
        self.sock.send_hci_cmd(cmd_pkt)

    def get_hci_filter(self):
        return self.sock.get_hci_filter()

    def new_hci_filter(self, ptype=None, event=None, opcode=None):
        return self.sock.new_hci_filter(ptype, event, opcode)

    def set_hci_filter(self, flt):
        self.sock.set_hci_filter(flt)

    def recv_hci_evt(self):
        return self.sock.recv_hci_evt()

class HCICoordinator(object):
    def serve(self):
        pass
