"""HCI event.
"""
from . import bluez
from .error import HCIParseError
from .utils import letoh8, letohs8, letoh16, letoh24


class HCIEvent(object):
    def __init__(self, code):
        super(HCIEvent, self).__init__()
        self.code = code

    def __str__(self):
        return '{}{}'.format(self.__class__.__name__, self.param_str())

    def param_str(self):
        return ''

    def unpack_param(self, buf, offset=0):
        raise NotImplementedError

    @staticmethod
    def get_pkt_size(buf, offset=0):
        return 2 + letoh8(buf, offset + 1)

    @staticmethod
    def parse(buf, offset=0):
        """Parse HCI event.
        
        offset is the start offset of event packet.
        """
        avail_len = len(buf) - offset
        code = letoh8(buf, offset)
        offset += 1
        plen = letoh8(buf, offset)
        offset += 1
        if avail_len  < 2 + plen:
            raise HCIParseError('not enough data to parse')
        if code == bluez.EVT_LE_META_EVENT:
            le_code = letoh8(buf, offset)
            offset += 1
            evt = _le_evt_table[le_code]()
        else:
            evt = _evt_table[code]()
        evt.unpack_param(buf, offset)
        return evt


class InquiryCompleteEvent(HCIEvent):
    def __init__(self):
        super(InquiryCompleteEvent, self).__init__(bluez.EVT_INQUIRY_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)

class DisconnectionCompleteEvent(HCIEvent):
    def __init__(self):
        super(DisconnectionCompleteEvent, self).__init__(bluez.EVT_DISCONN_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.reason = letoh8(buf, offset)

class ReadRemoteVersionInformationCompleteEvent(HCIEvent):
    def __init__(self):
        super(ReadRemoteVersionInformationCompleteEvent, self).__init__(bluez.EVT_READ_REMOTE_VERSION_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.version = letoh8(buf, offset)
        offset += 1
        self.manu_name = letoh16(buf, offset)
        offset += 2
        self.subversion = letoh16(buf, offset)

def _parse_cmd_complt_evt_param_status(evt, buf, offset):
    evt.status = letoh8(buf, offset)

def _parse_cmd_complt_evt_param_read_inquiry_mode(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.inquiry_mode = letoh8(buf, offset)

def _parse_cmd_complt_evt_param_read_bd_addr(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.bd_addr = buf[offset:offset+6]

def _parse_cmd_complt_evt_param_read_white_list_size(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.wlist_size = letoh8(buf, offset)

def _parse_cmd_complt_evt_param_le_read_buf_size(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.hc_le_acl_data_pkt_len = letoh16(buf, offset)
    offset += 2
    evt.hc_total_num_le_acl_data_pkts = letoh8(buf, offset)

def _parse_cmd_complt_evt_param_conn_handle(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.conn_handle = letoh16(buf, offset)

_cmd_complt_evt_param_parser = {
        0x0C01: _parse_cmd_complt_evt_param_status,
        0x0C03: _parse_cmd_complt_evt_param_status,
        0x0C44: _parse_cmd_complt_evt_param_read_inquiry_mode,
        0x0C45: _parse_cmd_complt_evt_param_status,
        0x1009: _parse_cmd_complt_evt_param_read_bd_addr,
        0x2001: _parse_cmd_complt_evt_param_status,
        0x2002: _parse_cmd_complt_evt_param_le_read_buf_size,
        0x2006: _parse_cmd_complt_evt_param_status,
        0x2008: _parse_cmd_complt_evt_param_status,
        0x200a: _parse_cmd_complt_evt_param_status,
        0x200e: _parse_cmd_complt_evt_param_status,
        0x200f: _parse_cmd_complt_evt_param_read_white_list_size,
        0x2010: _parse_cmd_complt_evt_param_status,
        0x2011: _parse_cmd_complt_evt_param_status,
        0x2012: _parse_cmd_complt_evt_param_status,
        0x2022: _parse_cmd_complt_evt_param_conn_handle,
}

class CommandCompleteEvent(HCIEvent):
    def __init__(self):
        super(CommandCompleteEvent, self).__init__(bluez.EVT_CMD_COMPLETE)

    def param_str(self):
        return '({}, 0x{:02x})'.format(self.num_hci_cmd_pkt, self.cmd_opcode)

    def unpack_param(self, buf, offset=0):
        self.num_hci_cmd_pkt = letoh8(buf, offset)
        offset += 1
        self.cmd_opcode = letoh16(buf, offset)
        offset += 2
        _cmd_complt_evt_param_parser[self.cmd_opcode](self, buf, offset)

class CommandStatusEvent(HCIEvent):
    def __init__(self):
        super(CommandStatusEvent, self).__init__(bluez.EVT_CMD_STATUS)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.num_hci_cmd_pkt = letoh8(buf, offset)
        offset += 1
        self.cmd_opcode = letoh16(buf, offset)

class NumberOfCompletedPacketsEvent(HCIEvent):
    def __init__(self):
        super(NumberOfCompletedPacketsEvent, self).__init__(bluez.EVT_NUM_COMP_PKTS)

    def unpack_param(self, buf, offset):
        self.num_handles = letoh8(buf, offset)
        offset += 1
        self.conn_handle = [0]*self.num_handles
        self.num_completed_pkts = [0]*self.num_handles
        for i in xrange(0, self.num_handles):
            self.conn_handle[i] = letoh16(buf, offset)
            offset += 2
            self.num_completed_pkts[i] = letoh16(buf, offset)
            offset += 2

class InquiryResultWithRSSIEvent(HCIEvent):
    def __init__(self):
        super(InquiryResultWithRSSIEvent, self).__init__(
                bluez.EVT_INQUIRY_RESULT_WITH_RSSI)

    def unpack_param(self, buf, offset):
        num_responses = letoh8(buf, offset)
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
            self.bd_addr[i] = buf[offset:offset+6]
            offset += 6
            self.page_scan_repetition_mode[i] = letoh8(buf, offset)
            offset += 1
            self.reserved[i] = letoh8(buf, offset)
            offset += 1
            self.class_of_dev[i] = letoh24(buf, offset)
            offset += 3
            self.clk_offset[i] = letoh16(buf, offset)
            offset += 2
            self.rssi[i] = letohs8(buf, offset)
            offset += 1
            i += 1

class LEMetaEvent(HCIEvent):
    def __init__(self, subevt_code):
        super(LEMetaEvent, self).__init__(bluez.EVT_LE_META_EVENT)
        self.subevt_code = subevt_code

class LEConnectionCompleteEvent(LEMetaEvent):
    def __init__(self):
        super(LEConnectionCompleteEvent, self).__init__(bluez.EVT_LE_CONN_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.role = letoh8(buf, offset)
        offset += 1
        self.peer_addr_type = letoh8(buf, offset)
        offset += 1
        self.peer_addr = buf[offset:offset+6]
        offset += 6
        self.conn_intvl = letoh16(buf, offset)
        offset += 2
        self.conn_latency = letoh16(buf, offset)
        offset += 2
        self.supv_timeout = letoh16(buf, offset)
        offset += 2
        self.master_clk_accuracy = letoh8(buf, offset)

class LEDataLengthChangeEvent(LEMetaEvent):
    def __init__(self):
        super(LEDataLengthChangeEvent, self).__init__(bluez.EVT_LE_DATA_LEN_CHANGE)

    def unpack_param(self, buf, offset):
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.max_tx_octets = letoh16(buf, offset)
        offset += 2
        self.max_tx_time = letoh16(buf, offset)
        offset += 2
        self.max_rx_octets = letoh16(buf, offset)
        offset += 2
        self.max_rx_time = letoh16(buf, offset)

_evt_table = {
        bluez.EVT_INQUIRY_COMPLETE: InquiryCompleteEvent,
        bluez.EVT_DISCONN_COMPLETE: DisconnectionCompleteEvent,
        bluez.EVT_READ_REMOTE_VERSION_COMPLETE: ReadRemoteVersionInformationCompleteEvent,
        bluez.EVT_CMD_COMPLETE: CommandCompleteEvent,
        bluez.EVT_CMD_STATUS: CommandStatusEvent,
        bluez.EVT_NUM_COMP_PKTS: NumberOfCompletedPacketsEvent,
        bluez.EVT_INQUIRY_RESULT_WITH_RSSI: InquiryResultWithRSSIEvent,
}

_le_evt_table = {
        bluez.EVT_LE_CONN_COMPLETE: LEConnectionCompleteEvent,
        bluez.EVT_LE_DATA_LEN_CHANGE: LEDataLengthChangeEvent,
}

def parse_hci_event(code, buf, offset=0):
    """Parse HCI event.
    
    offset is the start offset of event parameters.
    """
    if code == bluez.EVT_LE_META_EVENT:
        le_code = letoh8(buf, offset)
        offset += 1
        evt = _le_evt_table[le_code]()
    else:
        evt = _evt_table[code]()
    evt.unpack_param(buf, offset)
    return evt

