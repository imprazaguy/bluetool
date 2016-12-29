"""HCI event.
"""
from . import bluez
from . import command as btcmd
from .error import HCIError, HCIParseError, HCIEventNotImplementedError, HCILEEventNotImplementedError, HCICommandCompleteEventNotImplementedError
from .utils import letoh8, letohs8, letoh16, letoh24, letoh64


class HCIEvent(object):
    """Base HCI event object."""

    code = 0 # Event code

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
    code = bluez.EVT_INQUIRY_COMPLETE

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)

class ConnectionCompleteEvent(HCIEvent):
    code = bluez.EVT_CONN_COMPLETE

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
    code = bluez.EVT_CONN_REQUEST

    def unpack_param(self, buf, offset):
        self.bd_addr = buf[offset:offset+6]
        offset += 6
        self.cod = letoh24(buf, offset)
        offset += 3
        self.link_type = letoh8(buf, offset)

class DisconnectionCompleteEvent(HCIEvent):
    code = bluez.EVT_DISCONN_COMPLETE

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.reason = letoh8(buf, offset)

class RemoteNameRequestCompleteEvent(HCIEvent):
    code = bluez.EVT_REMOTE_NAME_REQ_COMPLETE

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.bd_addr = buf[offset:offset+6]
        offset += 6
        self.remote_name = buf[offset:]


class EncryptionChangeEvent(HCIEvent):
    code = bluez.EVT_ENCRYPT_CHANGE

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.enc_enabled = letoh8(buf, offset)


class ReadRemoteSupportedFeaturesCompleteEvent(HCIEvent):
    code = bluez.EVT_READ_REMOTE_FEATURES_COMPLETE

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.lmp_features = buf[offset:offset+8]


class ReadRemoteVersionInformationCompleteEvent(HCIEvent):
    code = bluez.EVT_READ_REMOTE_VERSION_COMPLETE

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


def _gen_cmd_complt_evt_param_parser_table(*args):
    cmd_map = {}
    for cmd in args:
        cmd_map[cmd.opcode()] = cmd
    return cmd_map

_cmd_complt_evt_param_parser = _gen_cmd_complt_evt_param_parser_table(
        btcmd.HCISetEventMask,
        btcmd.HCIReset,
        btcmd.HCIWriteLinkPolicySettings,
        btcmd.HCIReadStoredLinkKey,
        btcmd.HCIWritePageTimeout,
        btcmd.HCIReadScanEnable,
        btcmd.HCIWriteScanEnable,
        btcmd.HCIWritePageScanActivity,
        btcmd.HCIReadInquiryMode,
        btcmd.HCIWriteInquiryMode,
        btcmd.HCIReadLocalSupportedFeatures,
        btcmd.HCIReadLocalExtendedFeatures,
        btcmd.HCIReadBDAddr,
        btcmd.HCILESetEventMask,
        btcmd.HCILEReadBufferSize,
        btcmd.HCILESetAdvertisingParameters,
        btcmd.HCILESetAdvertisingData,
        btcmd.HCILESetAdvertiseEnable,
        btcmd.HCILECreateConnectionCancel,
        btcmd.HCILEReadWhiteListSize,
        btcmd.HCILEClearWhiteList,
        btcmd.HCILEAddDeviceToWhiteList,
        btcmd.HCILERemoveDeviceFromWhiteList,
        btcmd.HCILESetHostChannelClassification,
        btcmd.HCILELongTermKeyRequestReply,
        btcmd.HCILELongTermKeyRequestNegtiveReply,
        btcmd.HCILESetDataLength,
        btcmd.HCILEReadSuggestedDefaultDataLength,
        btcmd.HCILEWriteSuggestedDefaultDataLength)

def register_cmd_complt_evt(hci_cmd):
    _cmd_complt_evt_param_parser[hci_cmd.opcode()] = hci_cmd

class CommandCompleteEvent(HCIEvent):
    code = bluez.EVT_CMD_COMPLETE

    def param_str(self):
        return '({}, 0x{:02x})'.format(self.num_hci_cmd_pkt, self.cmd_opcode)

    def unpack_param(self, buf, offset=0):
        self.num_hci_cmd_pkt = letoh8(buf, offset)
        offset += 1
        self.cmd_opcode = letoh16(buf, offset)
        offset += 2
        try:
            _cmd_complt_evt_param_parser[self.cmd_opcode].unpack_ret_param(self, buf, offset)
        except KeyError:
            raise HCICommandCompleteEventNotImplementedError(self.cmd_opcode)

class CommandStatusEvent(HCIEvent):
    code = bluez.EVT_CMD_STATUS

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.num_hci_cmd_pkt = letoh8(buf, offset)
        offset += 1
        self.cmd_opcode = letoh16(buf, offset)

class RoleChangeEvent(HCIEvent):
    code = bluez.EVT_ROLE_CHANGE

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.bd_addr = buf[offset:offset+6]
        offset += 6
        self.new_role = letoh8(buf, offset)

class NumberOfCompletedPacketsEvent(HCIEvent):
    code = bluez.EVT_NUM_COMP_PKTS

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

class ModeChangeEvent(HCIEvent):
    code = bluez.EVT_MODE_CHANGE

    def unpack_param(self, buf, offset):
        self.status = letoh8(buf, offset)
        offset += 1
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.cur_mode = letoh8(buf, offset)
        offset += 1
        self.intvl = letoh16(buf, offset)

class MaxSlotsChangeEvent(HCIEvent):
    code = bluez.EVT_MAX_SLOTS_CHANGE

    def unpack_param(self, buf, offset):
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.lmp_max_slots = letoh8(buf, offset)

class PageScanRepetitionModeChangeEvent(HCIEvent):
    code = bluez.EVT_PSCAN_REP_MODE_CHANGE

    def unpack_param(self, buf, offset):
        self.bd_addr = buf[offset:offset+6]
        offset += 6
        self.pscan_rep_mode = letoh8(buf, offset)

class InquiryResultWithRSSIEvent(HCIEvent):
    code = bluez.EVT_INQUIRY_RESULT_WITH_RSSI

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
    code = bluez.EVT_READ_REMOTE_EXT_FEATURES_COMPLETE

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
    code = bluez.EVT_LE_META_EVENT
    subevt_code = 0

class LEConnectionCompleteEvent(LEMetaEvent):
    subevt_code = bluez.EVT_LE_CONN_COMPLETE

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
    subevt_code = bluez.EVT_LE_CONN_UPDATE_COMPLETE

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


class LELongTermKeyRequestEvent(LEMetaEvent):
    subevt_code = bluez.EVT_LE_LTK_REQUEST

    def unpack_param(self, buf, offset):
        self.conn_handle = letoh16(buf, offset)
        offset += 2
        self.rand = letoh64(buf, offset)
        offset += 8
        self.ediv = letoh16(buf, offset)


class LEDataLengthChangeEvent(LEMetaEvent):
    subevt_code = bluez.EVT_LE_DATA_LEN_CHANGE

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


class LEEnhancedConnectionCompleteEvent(LEMetaEvent):
    subevt_code = bluez.EVT_LE_ENHANCED_CONN_COMPLETE

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
        self.local_rpa = buf[offset:offset+6]
        offset += 6
        self.peer_rpa = buf[offset:offset+6]
        offset += 6
        self.conn_intvl = letoh16(buf, offset)
        offset += 2
        self.conn_latency = letoh16(buf, offset)
        offset += 2
        self.supv_timeout = letoh16(buf, offset)
        offset += 2
        self.master_clk_accuracy = letoh8(buf, offset)


class VendorEvent(HCIEvent):
    code = bluez.EVT_VENDOR

    def unpack_param(self, buf, offset):
        self.param = buf[offset:]

def _gen_evt_table(*args):
    evt_map = {}
    for evt in args:
        evt_map[evt.code] = evt
    return evt_map

_evt_table = _gen_evt_table(
        InquiryCompleteEvent,
        ConnectionCompleteEvent,
        ConnectionRequestEvent,
        DisconnectionCompleteEvent,
        RemoteNameRequestCompleteEvent,
        EncryptionChangeEvent,
        ReadRemoteSupportedFeaturesCompleteEvent,
        ReadRemoteVersionInformationCompleteEvent,
        CommandCompleteEvent,
        CommandStatusEvent,
        RoleChangeEvent,
        NumberOfCompletedPacketsEvent,
        ModeChangeEvent,
        MaxSlotsChangeEvent,
        PageScanRepetitionModeChangeEvent,
        InquiryResultWithRSSIEvent,
        ReadRemoteExtendedFeaturesCompleteEvent,
        VendorEvent)

def _gen_le_evt_table(*args):
    evt_map = {}
    for evt in args:
        evt_map[evt.subevt_code] = evt
    return evt_map

_le_evt_table = _gen_le_evt_table(
        LEConnectionCompleteEvent,
        LEConnectionUpdateCompleteEvent,
        LELongTermKeyRequestEvent,
        LEDataLengthChangeEvent,
        LEEnhancedConnectionCompleteEvent)

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

