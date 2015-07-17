"""HCI event.
"""
from . import bluez
from .error import HCIError, HCIParseError, HCIEventNotImplementedError, HCILEEventNotImplementedError, HCICommandCompleteEventNotImplementedError
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
        try:
            if code == bluez.EVT_LE_META_EVENT:
                le_code = letoh8(buf, offset)
                offset += 1
                try:
                    evt = _le_evt_table[le_code]()
                except KeyError:
                    raise HCILEEventNotImplementedError(le_code)
            else:
                try:
                    evt = _evt_table[code]()
                except KeyError:
                    raise HCIEventNotImplementedError(code)
            evt.unpack_param(buf, offset)
            return evt
        except HCIError as err:
            print str(err)
            return HCIEvent(code)

class InquiryCompleteEvent(HCIEvent):
    def __init__(self):
        super(InquiryCompleteEvent, self).__init__(bluez.EVT_INQUIRY_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)

class ConnectionCompleteEvent(HCIEvent):
    def __init__(self):
        super(ConnectionCompleteEvent, self).__init__(bluez.EVT_CONN_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.bd_addr = buf[offset:offset+6]
        offset += 6
        self.link_type = letoh8(buf, offset)
        offset += 1
        self.enc_enabled = letoh8(buf, offset)

class ConnectionRequestEvent(HCIEvent):
    def __init__(self):
        super(ConnectionRequestEvent, self).__init__(bluez.EVT_CONN_REQUEST)

    def unpack_param(self, buf, offset):
        self.bd_addr = buf[offset:offset+6]
        offset += 6
        self.cod = letoh24(buf, offset)
        offset += 3
        self.link_type = letoh8(buf, offset)

class DisconnectionCompleteEvent(HCIEvent):
    def __init__(self):
        super(DisconnectionCompleteEvent, self).__init__(bluez.EVT_DISCONN_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.reason = letoh8(buf, offset)

class RemoteNameRequestCompleteEvent(HCIEvent):
    def __init__(self):
        super(RemoteNameRequestCompleteEvent, self).__init__(bluez.EVT_REMOTE_NAME_REQ_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.bd_addr = buf[offset:offset+6]
        offset += 6
        self.remote_name = buf[offset:]

class ReadRemoteSupportedFeaturesCompleteEvent(HCIEvent):
    def __init__(self):
        super(ReadRemoteSupportedFeaturesCompleteEvent, self).__init__(bluez.EVT_READ_REMOTE_FEATURES_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.lmp_features = buf[offset:offset+8]

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

def _parse_cmd_complt_evt_param_read_stored_link_key(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.max_num_keys = letoh16(buf, offset)
    offset += 2
    evt.num_keys_read = letoh16(buf, offset)

def _parse_cmd_complt_evt_param_read_scan_enable(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.scan_enable = letoh8(buf, offset)

def _parse_cmd_complt_evt_param_read_inquiry_mode(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.inquiry_mode = letoh8(buf, offset)

def _parse_cmd_complt_evt_param_read_local_features(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.lmp_features = buf[offset:offset+8]

def _parse_cmd_complt_evt_param_read_local_ext_features(evt, buf, offset):
    evt.status = letoh8(buf, offset)
    offset += 1
    evt.page_num = letoh8(buf, offset)
    offset += 1
    evt.max_page_num = letoh8(buf, offset)
    offset += 1
    evt.ext_lmp_features = buf[offset:offset+8]

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
        0x0C0D: _parse_cmd_complt_evt_param_read_stored_link_key,
        0x0C18: _parse_cmd_complt_evt_param_status,
        0x0C19: _parse_cmd_complt_evt_param_read_scan_enable,
        0x0C1A: _parse_cmd_complt_evt_param_status,
        0x0C1C: _parse_cmd_complt_evt_param_status,
        0x0C44: _parse_cmd_complt_evt_param_read_inquiry_mode,
        0x0C45: _parse_cmd_complt_evt_param_status,
        0x1003: _parse_cmd_complt_evt_param_read_local_features,
        0x1004: _parse_cmd_complt_evt_param_read_local_ext_features,
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
        0x2014: _parse_cmd_complt_evt_param_status,
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
        try:
            _cmd_complt_evt_param_parser[self.cmd_opcode](self, buf, offset)
        except KeyError:
            raise HCICommandCompleteEventNotImplementedError(self.cmd_opcode)

class CommandStatusEvent(HCIEvent):
    def __init__(self):
        super(CommandStatusEvent, self).__init__(bluez.EVT_CMD_STATUS)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.num_hci_cmd_pkt = letoh8(buf, offset)
        offset += 1
        self.cmd_opcode = letoh16(buf, offset)

class RoleChangeEvent(HCIEvent):
    def __init__(self):
        super(RoleChangeEvent, self).__init__(bluez.EVT_ROLE_CHANGE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.bd_addr = buf[offset:offset+6]
        offset += 6
        self.new_role = letoh8(buf, offset)

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

class MaxSlotsChangeEvent(HCIEvent):
    def __init__(self):
        super(MaxSlotsChangeEvent, self).__init__(bluez.EVT_MAX_SLOTS_CHANGE)

    def unpack_param(self, buf, offset):
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.lmp_max_slots = letoh8(buf, offset)

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

class ReadRemoteExtendedFeaturesCompleteEvent(HCIEvent):
    def __init__(self):
        super(ReadRemoteExtendedFeaturesCompleteEvent, self).__init__(bluez.EVT_READ_REMOTE_EXT_FEATURES_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.page_num = letoh8(buf, offset)
        offset += 1
        self.max_page_num = letoh8(buf, offset)
        offset += 1
        self.ext_lmp_features = buf[offset:offset+8]

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

class LEConnectionUpdateCompleteEvent(LEMetaEvent):
    def __init__(self):
        super(LEConnectionUpdateCompleteEvent, self).__init__(
                bluez.EVT_LE_CONN_UPDATE_COMPLETE)

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.conn_intvl = letoh16(buf, offset)
        offset += 2
        self.conn_latency = letoh16(buf, offset)
        offset += 2
        self.supv_timeout = letoh16(buf, offset)

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
        bluez.EVT_CONN_COMPLETE: ConnectionCompleteEvent,
        bluez.EVT_CONN_REQUEST: ConnectionRequestEvent,
        bluez.EVT_DISCONN_COMPLETE: DisconnectionCompleteEvent,
        bluez.EVT_REMOTE_NAME_REQ_COMPLETE: RemoteNameRequestCompleteEvent,
        bluez.EVT_READ_REMOTE_FEATURES_COMPLETE: ReadRemoteSupportedFeaturesCompleteEvent,
        bluez.EVT_READ_REMOTE_VERSION_COMPLETE: ReadRemoteVersionInformationCompleteEvent,
        bluez.EVT_CMD_COMPLETE: CommandCompleteEvent,
        bluez.EVT_CMD_STATUS: CommandStatusEvent,
        bluez.EVT_ROLE_CHANGE: RoleChangeEvent,
        bluez.EVT_NUM_COMP_PKTS: NumberOfCompletedPacketsEvent,
        bluez.EVT_MAX_SLOTS_CHANGE: MaxSlotsChangeEvent,
        bluez.EVT_INQUIRY_RESULT_WITH_RSSI: InquiryResultWithRSSIEvent,
        bluez.EVT_READ_REMOTE_EXT_FEATURES_COMPLETE: ReadRemoteExtendedFeaturesCompleteEvent,
}

_le_evt_table = {
        bluez.EVT_LE_CONN_COMPLETE: LEConnectionCompleteEvent,
        bluez.EVT_LE_DATA_LEN_CHANGE: LEDataLengthChangeEvent,
        bluez.EVT_LE_CONN_UPDATE_COMPLETE: LEConnectionUpdateCompleteEvent,
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

