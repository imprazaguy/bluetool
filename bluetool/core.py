
import event
import struct
import bluetooth._bluetooth as bluez

class HCITask(object):
    def __init__(self, worker):
        self.worker = worker

    def run(self):
        """Perform actions."""
        raise NotImplementedError

class HCIWorker(object):
    evt_header_fmt = struct.Struct('<BBB')

    def __init__(self, sock):
        self.sock = sock

    def run(self):
        raise NotImplementedError

    def send_hci_cmd(self, cmd_pkt):
        cmd_pkt.send(self.sock)

    def get_hci_filter(self, **kwargs):
        if len(kwargs) == 0:
            return self.sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)
        flt = bluez.hci_filter_new()
        if 'ptype' in kwargs:
            bluez.hci_filter_set_ptype(flt, kwargs['ptype'])
        else:
            bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
        if 'event' in kwargs:
            if kwargs['event'] == 'all':
                bluez.hci_filter_all_events(flt)
            else:
                bluez.hci_filter_set_event(flt, kwargs['event'])
        if 'opcode' in kwargs:
            bluez.hci_filter_set_opcode(flt, kwargs['opcode'])
        return flt

    def set_hci_filter(self, flt):
        self.sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt)

    def recv_hci_evt(self, flt=None):
        if flt is not None:
            self.set_hci_filter(flt)
        buf = self.sock.recv(260)
        ptype, evt_code, plen = self.evt_header_fmt.unpack_from(buf)
        return event.parse_hci_event(evt_code, buf, self.evt_header_fmt.size)

class HCICoordinator(object):
    def serve(self):
        pass
