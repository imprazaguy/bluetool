# -*- coding: utf-8 -*-
"""HCI command.
"""
from . import bluez
from . import error
from .utils import letoh8, letoh16, htole8, htole16, htole24, htole64, count_bits


class HCICommand(object):
    """Base HCI command object."""

    ogf = 0 # Opcode group field (should be overridden by derived class)
    ocf = 0 # Opcode command field (should be overriden by derived class)

    def __str__(self):
        return self.__class__.__name__

    @classmethod
    def opcode(cls):
        return bluez.cmd_opcode_pack(cls.ogf, cls.ocf)

    def pack_param(self):
        """Pack command parameters.

        Subclass sould implement this method.
        """
        return None

    @staticmethod
    def get_pkt_size(buf, offset=0):
        return 3 + letoh8(buf, offset + 2)

    @staticmethod
    def parse(buf, offset=0):
        raise NotImplementedError


class CmdCompltEvtParamUnpacker(object):
    """Base helper class to unpack CommandCompleteEvent parameters.

    A specific HCICommand should inherit this class and override
    unpack_ret_param() to provide its own return parameters in the
    command complete event.
    """

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        evt.status = letoh8(buf, offset)
        offset += 1
        return offset


class HCILinkControlCommand(HCICommand):
    ogf = bluez.OGF_LINK_CTL

class HCIInquiry(HCILinkControlCommand):
    ocf = bluez.OCF_INQUIRY

    def __init__(self, lap, inquiry_len, num_responses):
        super(HCIInquiry, self).__init__()
        self.lap = lap
        self.inquiry_len = inquiry_len
        self.num_responses = num_responses

    def pack_param(self):
        return ''.join(
                (htole24(self.lap),
                    htole8(self.inquiry_len),
                    htole8(self.num_responses)))

class HCICreateConnection(HCILinkControlCommand):
    ocf = bluez.OCF_CREATE_CONN

    def __init__(self, bd_addr, pkt_type, page_scan_rep_mode, clk_offs, allow_role_switch):
        super(HCICreateConnection, self).__init__()
        self.bd_addr = bd_addr
        self.pkt_type = pkt_type
        self.page_scan_rep_mode = page_scan_rep_mode
        self.clk_offs = clk_offs
        self.allow_role_switch = allow_role_switch

    def pack_param(self):
        return ''.join(
                (self.bd_addr, htole16(self.pkt_type),
                    htole8(self.page_scan_rep_mode),
                    htole8(0x00), # Reserved
                    htole16(self.clk_offs),
                    htole8(self.allow_role_switch)))

class HCIDisconnect(HCILinkControlCommand):
    ocf = bluez.OCF_DISCONNECT

    def __init__(self, conn_handle, reason):
        super(HCIDisconnect, self).__init__()
        self.conn_handle = conn_handle
        self.reason = reason

    def pack_param(self):
        return ''.join((htole16(self.conn_handle), htole8(self.reason)))
 
class HCIAcceptConnectionRequest(HCILinkControlCommand):
    ocf = bluez.OCF_ACCEPT_CONN_REQ

    def __init__(self, bd_addr, role):
        super(HCIAcceptConnectionRequest, self).__init__()
        self.bd_addr = bd_addr
        self.role = role

    def pack_param(self):
        return ''.join((self.bd_addr, htole8(self.role)))


class HCIReadRemoteVersionInformation(HCILinkControlCommand):
    ocf = bluez.OCF_READ_REMOTE_VERSION

    def __init__(self, conn_handle):
        super(HCIReadRemoteVersionInformation, self).__init__()
        self.conn_handle = conn_handle

    def pack_param(self):
        return ''.join((htole16(self.conn_handle)))


class HCILinkPolicyCommand(HCICommand):
    ogf = bluez.OGF_LINK_POLICY

class HCISniffMode(HCILinkPolicyCommand):
    ocf = bluez.OCF_SNIFF_MODE

    def __init__(self, conn_handle, sniff_max_intvl, sniff_min_intvl, sniff_attempt, sniff_timeout):
        super(HCISniffMode, self).__init__()
        self.conn_handle = conn_handle
        self.sniff_max_intvl = sniff_max_intvl
        self.sniff_min_intvl = sniff_min_intvl
        self.sniff_attempt = sniff_attempt
        self.sniff_timeout = sniff_timeout

    def pack_param(self):
        return ''.join((
            htole16(self.conn_handle),
            htole16(self.sniff_max_intvl),
            htole16(self.sniff_min_intvl),
            htole16(self.sniff_attempt),
            htole16(self.sniff_timeout)))

class HCIExitSniffMode(HCILinkPolicyCommand):
    ocf = bluez.OCF_EXIT_SNIFF_MODE

    def __init__(self, conn_handle):
        super(HCIExitSniffMode, self).__init__()
        self.conn_handle = conn_handle

    def pack_param(self):
        return ''.join((htole16(self.conn_handle)))

class HCIWriteLinkPolicySettings(HCILinkPolicyCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_WRITE_LINK_POLICY

    def __init__(self, conn_handle, link_policy):
        super(HCIWriteLinkPolicySettings, self).__init__()
        self.conn_handle = conn_handle
        self.link_policy = link_policy

    def pack_param(self):
        return ''.join((
            htole16(self.conn_handle),
            htole16(self.link_policy)))

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCIWriteLinkPolicySettings, cls).unpack_ret_param(evt, buf, offset)
        evt.conn_handle = letoh16(buf, offset)

class HCIControllerCommand(HCICommand):
    ogf = bluez.OGF_HOST_CTL

class HCISetEventMask(HCIControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_SET_EVENT_MASK

    def __init__(self, event_mask):
        super(HCISetEventMask, self).__init__()
        self.event_mask = event_mask

    def pack_param(self):
        return htole64(self.event_mask)

class HCIReset(HCIControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_RESET

class HCIReadStoredLinkKey(HCIControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_READ_STORED_LINK_KEY

    def __init__(self, bd_addr, read_all_flag):
        super(HCIReadStoredLinkKey, self).__init__()
        self.bd_addr = bd_addr
        self.read_all_flag = read_all_flag

    def pack_param(self):
        return ''.join((self.bd_addr, htole8(self.read_all_flag)))

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCIReadStoredLinkKey, cls).unpack_ret_param(evt, buf, offset)
        evt.max_num_keys = letoh16(buf, offset)
        offset += 2
        evt.num_keys_read = letoh16(buf, offset)

class HCIWritePageTimeout(HCIControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_WRITE_PAGE_TIMEOUT

    def __init__(self, page_timeout):
        super(HCIWritePageTimeout, self).__init__()
        self.page_timeout = page_timeout

    def pack_param(self):
        return ''.join((htole16(self.page_timeout)))

class HCIReadScanEnable(HCIControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_READ_SCAN_ENABLE

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCIReadScanEnable, cls).unpack_ret_param(evt, buf, offset)
        evt.scan_enable = letoh8(buf, offset)

class HCIWriteScanEnable(HCIControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_WRITE_SCAN_ENABLE

    def __init__(self, scan_enable):
        super(HCIWriteScanEnable, self).__init__()
        self.scan_enable = scan_enable

    def pack_param(self):
        return htole8(self.scan_enable)

class HCIWritePageScanActivity(HCIControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_WRITE_PAGE_ACTIVITY

    def __init__(self, page_scan_intvl, page_scan_window):
        super(HCIWritePageScanActivity, self).__init__()
        self.page_scan_intvl = page_scan_intvl
        self.page_scan_window = page_scan_window

    def pack_param(self):
        return ''.join(
                (htole16(self.page_scan_intvl),
                    htole16(self.page_scan_window)))

class HCIReadInquiryMode(HCIControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_READ_INQUIRY_MODE

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCIReadInquiryMode, cls).unpack_ret_param(evt, buf, offset)
        evt.inquiry_mode = letoh8(buf, offset)

class HCIWriteInquiryMode(HCIControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_WRITE_INQUIRY_MODE

    def __init__(self, mode):
        super(HCIWriteInquiryMode, self).__init__()
        self.mode = mode

    def pack_param(self):
        return htole8(self.mode)


class HCIInfoParamCommand(HCICommand):
    ogf = bluez.OGF_INFO_PARAM

class HCIReadLocalSupportedFeatures(HCIInfoParamCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_READ_LOCAL_FEATURES

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCIReadLocalSupportedFeatures, cls).unpack_ret_param(evt, buf, offset)
        evt.lmp_features = buf[offset:offset+8]

class HCIReadLocalExtendedFeatures(HCIInfoParamCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_READ_LOCAL_EXT_FEATURES

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCIReadLocalExtendedFeatures, cls).unpack_ret_param(evt, buf, offset)
        evt.page_num = letoh8(buf, offset)
        offset += 1
        evt.max_page_num = letoh8(buf, offset)
        offset += 1
        evt.ext_lmp_features = buf[offset:offset+8]

class HCIReadBDAddr(HCIInfoParamCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_READ_BD_ADDR

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCIReadBDAddr, cls).unpack_ret_param(evt, buf, offset)
        evt.bd_addr = buf[offset:offset+6]


class HCILEControllerCommand(HCICommand):
    ogf = bluez.OGF_LE_CTL

class HCILESetEventMask(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_EVENT_MASK

    def __init__(self, le_evt_mask):
        super(HCILESetEventMask, self).__init__()
        self.le_evt_mask = le_evt_mask

    def pack_param(self):
        return htole64(self.le_evt_mask)

class HCILEReadBufferSize(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_READ_BUFFER_SIZE

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILEReadBufferSize, cls).unpack_ret_param(evt, buf, offset)
        evt.hc_le_acl_data_pkt_len = letoh16(buf, offset)
        offset += 2
        evt.hc_total_num_le_acl_data_pkts = letoh8(buf, offset)


class HCILESetAdvertisingParameters(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_ADVERTISING_PARAMETERS

    def __init__(self, adv_intvl_min, adv_intvl_max, adv_type, own_addr_type,
                 direct_addr_type, direct_addr, adv_channel_map,
                 adv_filter_policy):
        super(HCILESetAdvertisingParameters, self).__init__()
        self.adv_intvl_min = adv_intvl_min
        self.adv_intvl_max = adv_intvl_max
        self.adv_type = adv_type
        self.own_addr_type = own_addr_type
        self.direct_addr_type = direct_addr_type
        self.direct_addr = direct_addr
        self.adv_channel_map = adv_channel_map
        self.adv_filter_policy = adv_filter_policy

    def pack_param(self):
        return ''.join((
            htole16(self.adv_intvl_min),
            htole16(self.adv_intvl_max),
            htole8(self.adv_type),
            htole8(self.own_addr_type),
            htole8(self.direct_addr_type),
            self.direct_addr,
            htole8(self.adv_channel_map),
            htole8(self.adv_filter_policy)))


class HCILEReadAdvertisingChannelTxPower(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_READ_ADVERTISING_CHANNEL_TX_POWER

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILEReadAdvertisingChannelTxPower,
                       cls).unpack_ret_param(evt, buf, offset)
        evt.transmit_power_level = letoh8(buf, offset)


class HCILESetAdvertisingData(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_ADVERTISING_DATA

    def __init__(self, adv_data):
        super(HCILESetAdvertisingData, self).__init__()
        self.adv_data_len = len(adv_data)
        self.adv_data = ''.join((adv_data, '\x00'*(31 - self.adv_data_len)))

    def pack_param(self):
        return ''.join((htole8(self.adv_data_len), self.adv_data))


class HCILESetScanResponseData(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_SCAN_RESPONSE_DATA

    def __init__(self, scan_rsp_data):
        super(HCILESetScanResponseData, self).__init__()
        self.scan_rsp_data_len = len(scan_rsp_data)
        self.scan_rsp_data = ''.join((
            scan_rsp_data, '\x00'*(31 - self.scan_rsp_data_len)))

    def pack_param(self):
        return ''.join((htole8(self.scan_rsp_data_len), self.scan_rsp_data))


class HCILESetAdvertiseEnable(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_ADVERTISE_ENABLE

    def __init__(self, adv_enable):
        super(HCILESetAdvertiseEnable, self).__init__()
        self.adv_enable = adv_enable

    def pack_param(self):
        return htole8(self.adv_enable)


class HCILESetScanParameters(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_SCAN_PARAMETERS

    def __init__(self, scan_type, scan_intvl, scan_window, own_addr_type,
                 scan_filter_policy):
        super(HCILESetScanParameters, self).__init__()
        self.scan_type = scan_type
        self.scan_intvl = scan_intvl
        self.scan_window = scan_window
        self.own_addr_type = own_addr_type
        self.scan_filter_policy = scan_filter_policy

    def pack_param(self):
        return ''.join((
            htole8(self.scan_type),
            htole16(self.scan_intvl),
            htole16(self.scan_window),
            htole8(self.own_addr_type),
            htole8(self.scan_filter_policy)))


class HCILESetScanEnable(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_SCAN_ENABLE

    def __init__(self, enable, filter_duplicate):
        super(HCILESetScanEnable, self).__init__()
        self.enable = enable
        self.filter_duplicate = filter_duplicate

    def pack_param(self):
        return ''.join((
            htole8(self.enable),
            htole8(self.filter_duplicate)))


class HCILECreateConnection(HCILEControllerCommand):
    ocf = bluez.OCF_LE_CREATE_CONN

    def __init__(self, scan_intvl, scan_win, init_filter_policy,
                 peer_addr_type, peer_addr, own_addr_type, conn_intvl_min,
                 conn_intvl_max, conn_latency, supv_timeout, min_ce_len,
                 max_ce_len):
        super(HCILECreateConnection, self).__init__()
        self.scan_intvl = scan_intvl
        self.scan_win = scan_win
        self.init_filter_policy = init_filter_policy
        self.peer_addr_type = peer_addr_type
        self.peer_addr = peer_addr
        self.own_addr_type = own_addr_type
        self.conn_intvl_min = conn_intvl_min
        self.conn_intvl_max = conn_intvl_max
        self.conn_latency = conn_latency
        self.supv_timeout = supv_timeout
        self.min_ce_len = min_ce_len
        self.max_ce_len = max_ce_len

    def pack_param(self):
        return ''.join((
            htole16(self.scan_intvl),
            htole16(self.scan_win),
            htole8(self.init_filter_policy),
            htole8(self.peer_addr_type),
            self.peer_addr,
            htole8(self.own_addr_type),
            htole16(self.conn_intvl_min),
            htole16(self.conn_intvl_max),
            htole16(self.conn_latency),
            htole16(self.supv_timeout),
            htole16(self.min_ce_len),
            htole16(self.max_ce_len)))


class HCILECreateConnectionCancel(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_CREATE_CONN_CANCEL

class HCILEReadWhiteListSize(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_READ_WHITE_LIST_SIZE

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILEReadWhiteListSize, cls).unpack_ret_param(evt, buf, offset)
        evt.wlist_size = letoh8(buf, offset)

class HCILEClearWhiteList(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_CLEAR_WHITE_LIST

class HCILEAddDeviceToWhiteList(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_ADD_DEVICE_TO_WHITE_LIST

    def __init__(self, addr_type, addr):
        super(HCILEAddDeviceToWhiteList, self).__init__()
        self.addr_type = addr_type
        self.addr = addr

    def pack_param(self):
        return ''.join((htole8(self.addr_type), self.addr))

class HCILERemoveDeviceFromWhiteList(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_REMOVE_DEVICE_FROM_WHITE_LIST

    def __init__(self, addr_type, addr):
        super(HCILERemoveDeviceFromWhiteList, self).__init__()
        self.addr_type = addr_type
        self.addr = addr

    def pack_param(self):
        return ''.join((htole8(self.addr_type), self.addr))

class HCILEConnectionUpdate(HCILEControllerCommand):
    ocf = bluez.OCF_LE_CONN_UPDATE

    def __init__(self, conn_handle, conn_intvl_min, conn_intvl_max,
            conn_latency, supv_timeout, min_ce_len, max_ce_len):
        super(HCILEConnectionUpdate, self).__init__()
        self.conn_handle = conn_handle
        self.conn_intvl_min = conn_intvl_min
        self.conn_intvl_max = conn_intvl_max
        self.conn_latency = conn_latency
        self.supv_timeout = supv_timeout
        self.min_ce_len = min_ce_len
        self.max_ce_len = max_ce_len

    def pack_param(self):
        return ''.join((
            htole16(self.conn_handle),
            htole16(self.conn_intvl_min),
            htole16(self.conn_intvl_max),
            htole16(self.conn_latency),
            htole16(self.supv_timeout),
            htole16(self.min_ce_len),
            htole16(self.max_ce_len)))

class HCILESetHostChannelClassification(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_HOST_CHANNEL_CLASSIFICATION

    def __init__(self, channel_map):
        super(HCILESetHostChannelClassification, self).__init__()
        self.channel_map = channel_map

    def pack_param(self):
        return ''.join((self.channel_map))


class HCILEStartEncryption(HCILEControllerCommand):
    ocf = bluez.OCF_LE_START_ENCRYPTION

    def __init__(self, conn_handle, rand, ediv, ltk):
        super(HCILEStartEncryption, self).__init__()
        self.conn_handle = conn_handle
        self.rand = rand
        self.ediv = ediv
        self.ltk = ltk

    def pack_param(self):
        return ''.join((
            htole16(self.conn_handle),
            htole64(self.rand),
            htole16(self.ediv),
            self.ltk))


class HCILELongTermKeyRequestReply(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_LTK_REPLY

    def __init__(self, conn_handle, ltk):
        super(HCILELongTermKeyRequestReply, self).__init__()
        self.conn_handle = conn_handle
        self.ltk = ltk

    def pack_param(self):
        return ''.join((
            htole16(self.conn_handle),
            self.ltk))

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILELongTermKeyRequestReply, cls).unpack_ret_param(
            evt, buf, offset)
        evt.conn_handle = letoh16(buf, offset)


class HCILELongTermKeyRequestNegtiveReply(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_LTK_NEG_REPLY

    def __init__(self, conn_handle):
        super(HCILELongTermKeyRequestNegtiveReply, self).__init__()
        self.conn_handle = conn_handle

    def pack_param(self):
        return ''.join((htole16(self.conn_handle)))

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILELongTermKeyRequestNegtiveReply,
                       cls).unpack_ret_param(evt, buf, offset)
        evt.conn_handle = letoh16(buf, offset)


class HCILESetDataLength(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_DATA_LEN

    def __init__(self, conn_handle, tx_octets, tx_time):
        super(HCILESetDataLength, self).__init__()
        self.conn_handle = conn_handle
        self.tx_octets = tx_octets
        self.tx_time = tx_time

    def pack_param(self):
        return ''.join((htole16(self.conn_handle),
            htole16(self.tx_octets),
            htole16(self.tx_time)))

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILESetDataLength, cls).unpack_ret_param(evt, buf, offset)
        evt.conn_handle = letoh16(buf, offset)

class HCILEReadSuggestedDefaultDataLength(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_READ_DEFAULT_DATA_LEN

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILEReadSuggestedDefaultDataLength, cls).unpack_ret_param(evt, buf, offset)
        evt.sug_max_tx_octets = letoh16(buf, offset)
        offset += 2
        evt.sug_max_tx_time = letoh16(buf, offset)

class HCILEWriteSuggestedDefaultDataLength(HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_WRITE_DEFAULT_DATA_LEN

    def __init__(self, sug_max_tx_octets, sug_max_tx_time):
        super(HCILEWriteSuggestedDefaultDataLength, self).__init__()
        self.sug_max_tx_octets = sug_max_tx_octets
        self.sug_max_tx_time = sug_max_tx_time

    def pack_param(self):
        return ''.join((htole16(self.sug_max_tx_octets), htole16(self.sug_max_tx_time)))


class HCILESetExtendedAdvertisingParameters(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_EXT_ADVERTISING_PARAMETERS

    def __init__(self, adv_handle, adv_evt_prop, pri_adv_intvl_min,
                 pri_adv_intvl_max, pri_adv_ch_map, own_addr_type,
                 peer_addr_type, peer_addr, adv_filter_policy, adv_tx_power,
                 pri_adv_phy, sec_adv_max_skip, sec_adv_phy, adv_sid,
                 scan_req_notif_enable):
        super(HCILESetExtendedAdvertisingParameters, self).__init__()
        self.adv_handle = adv_handle
        self.adv_evt_prop = adv_evt_prop
        self.pri_adv_intvl_min = pri_adv_intvl_min
        self.pri_adv_intvl_max = pri_adv_intvl_max
        self.pri_adv_ch_map = pri_adv_ch_map
        self.own_addr_type = own_addr_type
        self.peer_addr_type = peer_addr_type
        self.peer_addr = peer_addr
        self.adv_filter_policy = adv_filter_policy
        self.adv_tx_power = adv_tx_power
        self.pri_adv_phy = pri_adv_phy
        self.sec_adv_max_skip = sec_adv_max_skip
        self.sec_adv_phy = sec_adv_phy
        self.adv_sid = adv_sid
        self.scan_req_notif_enable = scan_req_notif_enable

    def pack_param(self):
        return ''.join((
            htole8(self.adv_handle),
            htole16(self.adv_evt_prop),
            htole24(self.pri_adv_intvl_min),
            htole24(self.pri_adv_intvl_max),
            htole8(self.pri_adv_ch_map),
            htole8(self.own_addr_type),
            htole8(self.peer_addr_type),
            self.peer_addr,
            htole8(self.adv_filter_policy),
            htole8(self.adv_tx_power),
            htole8(self.pri_adv_phy),
            htole8(self.sec_adv_max_skip),
            htole8(self.sec_adv_phy),
            htole8(self.adv_sid),
            htole8(self.scan_req_notif_enable)))

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILESetExtendedAdvertisingParameters,
                       cls).unpack_ret_param(evt, buf, offset)
        evt.selected_tx_power = letoh8(buf, offset)


class HCILESetExtendedAdvertisingData(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_EXT_ADVERTISING_DATA

    def __init__(self, adv_handle, operation, frag_pref, adv_data):
        super(HCILESetExtendedAdvertisingData, self).__init__()
        self.adv_handle = adv_handle
        self.operation = operation
        self.frag_pref = frag_pref
        self.adv_data_len = len(adv_data)
        self.adv_data = adv_data

    def pack_param(self):
        return ''.join((
            htole8(self.adv_handle),
            htole8(self.operation),
            htole8(self.frag_pref),
            htole8(self.adv_data_len),
            self.adv_data))


class HCILESetExtendedScanResponseData(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_EXT_SCAN_RESPONSE_DATA

    def __init__(self, adv_handle, operation, frag_pref, scan_rsp_data):
        super(HCILESetExtendedScanResponseData, self).__init__()
        self.adv_handle = adv_handle
        self.operation = operation
        self.frag_pref = frag_pref
        self.scan_rsp_data_len = len(scan_rsp_data)
        self.scan_rsp_data = scan_rsp_data

    def pack_param(self):
        return ''.join((
            htole8(self.adv_handle),
            htole8(self.operation),
            htole8(self.frag_pref),
            htole8(self.scan_rsp_data_len),
            self.scan_rsp_data))


class HCILESetExtendedAdvertisingEnable(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_EXT_ADVERTISING_ENABLE

    class AdvSetParam(object):
        def __init__(self, adv_handle, duration, max_ext_adv_events):
            self.adv_handle = adv_handle
            self.duration = duration
            self.max_ext_adv_events = max_ext_adv_events

        def pack_param(self):
            return ''.join((
                htole8(self.adv_handle),
                htole16(self.duration),
                htole8(self.max_ext_adv_events)))

    def __init__(self, enable, num_sets, *args):
        super(HCILESetExtendedAdvertisingEnable, self).__init__()
        if len(args) != 3 * num_sets:
            raise error.HCIInvalidCommandParametersError(self)
        self.enable = enable
        self.num_sets = num_sets
        self.adv_set = [None] * num_sets
        for i in xrange(0, num_sets):
            self.adv_set[i] = HCILESetExtendedAdvertisingEnable.AdvEnableParam(
                args[3 * i], args[3 * i + 1], args[3 * i + 2])

    def pack_param(self):
        return ''.join((
            htole8(self.enable),
            htole8(self.num_sets),
            ''.join(o.pack_param() for o in self.adv_set)))


class HCILEReadMaximumAdvertisingDataLength(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_READ_MAX_ADVERTISING_DATA_LEN

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILEReadMaximumAdvertisingDataLength,
                       cls).unpack_ret_param(evt, buf, offset)
        evt.max_adv_data_len = letoh16(buf, offset)


class HCILEReadNumberOfSupportedAdvertisingSets(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_READ_NUM_SUPPORTED_ADVERTISING_SETS

    @classmethod
    def unpack_ret_param(cls, evt, buf, offset):
        offset = super(HCILEReadNumberOfSupportedAdvertisingSets,
                       cls).unpack_ret_param(evt, buf, offset)
        evt.num_supported_adv_sets = letoh8(buf, offset)


class HCILERemoveAdvertisingSet(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_REMOVE_ADVERTISING_SET

    def __init__(self, adv_handle):
        super(HCILERemoveAdvertisingSet, self).__init__()
        self.adv_handle = adv_handle

    def pack_param(self):
        return ''.join((htole8(self.adv_handle)))


class HCILEClearAdvertisingSets(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_CLEAR_ADVERTISING_SET


class HCILESetExtendedScanParameters(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_EXT_SCAN_PARAMETERS

    class ScanPhyParam(object):
        def __init__(self, scan_type, scan_intvl, scan_window):
            self.scan_type = scan_type
            self.scan_intvl = scan_intvl
            self.scan_window = scan_window

        def pack_param(self):
            return ''.join((
                htole8(self.scan_type),
                htole16(self.scan_intvl),
                htole16(self.scan_window)))

    def __init__(self, own_addr_type, scan_filter_policy, scan_phys, *args):
        super(HCILESetExtendedScanParameters, self).__init__()
        num_scan_phys = count_bits(scan_phys)
        if len(args) != 3 * num_scan_phys:
            raise error.HCIInvalidCommandParametersError(self)
        self.own_addr_type = own_addr_type
        self.scan_filter_policy = scan_filter_policy
        self.scan_phys = scan_phys
        self.scan_param = [None] * num_scan_phys
        for i in xrange(0, num_scan_phys):
            self.scan_param[i] = HCILESetExtendedScanParameters.ScanPhyParam(
                *args[3 * i:3 * (i + 1)])

    def pack_param(self):
        return ''.join((
            htole8(self.own_addr_type),
            htole8(self.scan_filter_policy),
            htole8(self.scan_phys),
            ''.join(o.pack_param() for o in self.scan_param)))


class HCILESetExtendedScanEnable(
        HCILEControllerCommand, CmdCompltEvtParamUnpacker):
    ocf = bluez.OCF_LE_SET_EXT_SCAN_ENABLE

    def __init__(self, enable, filter_duplicate, duration, period):
        super(HCILESetExtendedScanEnable, self).__init__()
        self.enable = enable
        self.filter_duplicate = filter_duplicate
        self.duration = duration
        self.period = period

    def pack_param(self):
        return ''.join((
            htole8(self.enable),
            htole8(self.filter_duplicate),
            htole16(self.duration),
            htole16(self.period)))


class HCILEExtendedCreateConnection(HCILEControllerCommand):
    ocf = bluez.OCF_LE_EXT_CREATE_CONN

    class InitPhyParam(object):
        def __init__(self, scan_intvl, scan_window, conn_intvl_min,
                     conn_intvl_max, conn_latency, supv_timeout, min_ce_len,
                     max_ce_len):
            self.scan_intvl = scan_intvl
            self.scan_window = scan_window
            self.conn_intvl_min = conn_intvl_min
            self.conn_intvl_max = conn_intvl_max
            self.conn_latency = conn_latency
            self.supv_timeout = supv_timeout
            self.min_ce_len = min_ce_len
            self.max_ce_len = max_ce_len

        def pack_param(self):
            return ''.join((
                htole16(self.scan_intvl),
                htole16(self.scan_window),
                htole16(self.conn_intvl_min),
                htole16(self.conn_intvl_max),
                htole16(self.conn_latency),
                htole16(self.supv_timeout),
                htole16(self.min_ce_len),
                htole16(self.max_ce_len)))

    def __init__(self, init_filter_policy, own_addr_type, peer_addr_type,
                 peer_addr, init_phys, *args):
        super(HCILEExtendedCreateConnection, self).__init__()
        num_init_phys = count_bits(init_phys)
        if len(args) != 8 * num_init_phys:
            raise error.HCIInvalidCommandParametersError(self)
        self.init_filter_policy = init_filter_policy
        self.own_addr_type = own_addr_type
        self.peer_addr_type = peer_addr_type
        self.peer_addr = peer_addr
        self.init_phys = init_phys
        self.init_param = [None] * num_init_phys
        for i in xrange(0, num_init_phys):
            self.init_param[i] = HCILEExtendedCreateConnection.InitPhyParam(
                *args[8 * i:8 * (i + 1)])

    def pack_param(self):
        return ''.join((
            htole8(self.init_filter_policy),
            htole8(self.own_addr_type),
            htole8(self.peer_addr_type),
            self.peer_addr,
            htole8(self.init_phys),
            ''.join(o.pack_param() for o in self.init_param)))


class HCIVendorCommand(HCICommand):
    ogf = bluez.OGF_VENDOR_CMD
