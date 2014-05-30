"""HCI event.
"""

import struct
import bluetooth._bluetooth as bluez

class HCIEventParseError(Exception):
    def __init__(self, msg=None):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class HCIEvent(object):
    def __init__(self, code):
        self.code = code

    def unpack_param(self, buf, offset=0):
        raise NotImplementedError

def _parse_hci_cmd_complt_evt_param_status(evt, buf, offset):
    evt.status = struct.unpack_from("<B", buf, offset)[0]

def _parse_hci_cmd_complt_evt_param_read_inquiry_mode(evt, buf, offset):
    evt.status, evt.inquiry_mode = struct.unpack_from("<BB", buf, offset)

class HCICommandCompleteEvent(HCIEvent):
    param_fmt = struct.Struct('<BH')
    ret_param_parser = {
            0x0C44: _parse_hci_cmd_complt_evt_param_read_inquiry_mode,
            0x0C45: _parse_hci_cmd_complt_evt_param_status,
    }

    def __init__(self):
        super(HCICommandCompleteEvent, self).__init__(bluez.EVT_CMD_COMPLETE)

    def unpack_param(self, buf, offset=0):
        self.num_hci_cmd_pkt, self.cmd_opcode = self.param_fmt.unpack_from(buf, offset)
        self.ret_param_parser[self.cmd_opcode](self, buf, offset + self.param_fmt.size)

_evt_table = {
        bluez.EVT_CMD_COMPLETE: HCICommandCompleteEvent,
}

def parse_hci_event(evt_code, buf, offset):
    """Parse HCI event.
    
    offset is the start offset of event parameters.
    """
    evt = _evt_table[evt_code]()
    evt.unpack_param(buf, offset)
    return evt

