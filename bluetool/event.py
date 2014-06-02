"""HCI event.
"""

import struct
import bluetooth._bluetooth as bluez

from .utils import letohs8, letoh16, letoh24

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

    @staticmethod
    def get_pkt_size(buf, offset=0):
        return 2 + ord(buf[offset + 1])

class HCIInquiryCompleteEvent(HCIEvent):
    def __init__(self):
        super(HCIInquiryCompleteEvent, self).__init__(bluez.EVT_INQUIRY_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = ord(buf[offset])

def _parse_hci_cmd_complt_evt_param_status(evt, buf, offset):
    evt.status = ord(buf[offset])

def _parse_hci_cmd_complt_evt_param_read_inquiry_mode(evt, buf, offset):
    evt.status = ord(buf[offset])
    offset += 1
    evt.inquiry_mode = ord(buf[offset])

class HCICommandCompleteEvent(HCIEvent):
    ret_param_parser = {
            0x0C44: _parse_hci_cmd_complt_evt_param_read_inquiry_mode,
            0x0C45: _parse_hci_cmd_complt_evt_param_status,
    }

    def __init__(self):
        super(HCICommandCompleteEvent, self).__init__(bluez.EVT_CMD_COMPLETE)

    def unpack_param(self, buf, offset=0):
        self.num_hci_cmd_pkt = ord(buf[offset])
        offset += 1
        self.cmd_opcode = letoh16(buf, offset)
        offset += 2
        self.ret_param_parser[self.cmd_opcode](self, buf, offset)

class HCICommandStatusEvent(HCIEvent):
    def __init__(self):
        super(HCICommandStatusEvent, self).__init__(bluez.EVT_CMD_STATUS)

    def unpack_param(self, buf, offset):
        self.status = ord(buf[offset])
        offset += 1
        self.num_hci_cmd_pkt = ord(buf[offset])
        offset += 1
        self.cmd_opcode = letoh16(buf, offset)

class HCIInquiryResultWithRSSIEvent(HCIEvent):
    def __init__(self):
        super(HCIInquiryResultWithRSSIEvent, self).__init__(
                bluez.EVT_INQUIRY_RESULT_WITH_RSSI)

    def unpack_param(self, buf, offset):
        num_responses = ord(buf[offset])
        offset += 1
        self.num_responses = num_responses
        self.bd_addr = [None]*num_responses
        self.page_scan_repetition_mode = [0]*num_responses
        self.reserved = [0]*num_responses
        self.class_of_dev = [0]*num_responses
        self.clk_offset = [0]*num_responses
        self.rssi = [0]*num_responses
        i = 0
        while i < self.num_responses:
            self.bd_addr[i] = str(buf[offset:offset+6])
            offset += 6
            self.page_scan_repetition_mode[i] = ord(buf[offset])
            offset += 1
            self.reserved[i] = ord(buf[offset])
            offset += 1
            self.class_of_dev[i] = letoh24(buf, offset)
            offset += 3
            self.clk_offset[i] = letoh16(buf, offset)
            offset += 2
            self.rssi[i] = letohs8(buf, offset)
            offset += 1
            i += 1

_evt_table = {
        bluez.EVT_INQUIRY_COMPLETE: HCIInquiryCompleteEvent,
        bluez.EVT_CMD_COMPLETE: HCICommandCompleteEvent,
        bluez.EVT_CMD_STATUS: HCICommandStatusEvent,
        bluez.EVT_INQUIRY_RESULT_WITH_RSSI: HCIInquiryResultWithRSSIEvent,
}

def parse_hci_event(code, buf, offset=0):
    """Parse HCI event.
    
    offset is the start offset of event parameters.
    """
    evt = _evt_table[code]()
    evt.unpack_param(buf, offset)
    return evt

