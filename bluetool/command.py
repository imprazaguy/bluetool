# -*- coding: utf-8 -*-
"""HCI command.
"""
from . import bluez
from .utils import letoh8, htole8, htole16, htole24, htole64


class HCICommand(object):
    """Base HCI command object."""

    def __init__(self, ogf, ocf):
        super(HCICommand, self).__init__()
        self.ogf = ogf
        self.ocf = ocf

    def __str__(self):
        return self.__class__.__name__

    @property
    def opcode(self):
        return bluez.cmd_opcode_pack(self.ogf, self.ocf)

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


class HCILinkControlCommand(HCICommand):
    def __init__(self, ocf):
        super(HCILinkControlCommand, self).__init__(bluez.OGF_LINK_CTL, ocf)

class HCIInquiry(HCILinkControlCommand):
    def __init__(self, lap, inquiry_len, num_responses):
        super(HCIInquiry, self).__init__(bluez.OCF_INQUIRY)
        self.lap = lap
        self.inquiry_len = inquiry_len
        self.num_responses = num_responses

    def pack_param(self):
        return ''.join(
                (htole24(self.lap),
                    htole8(self.inquiry_len),
                    htole8(self.num_responses)))

class HCICreateConnection(HCILinkControlCommand):
    def __init__(self, bd_addr, pkt_type, page_scan_rep_mode, clk_offs, allow_role_switch):
        super(HCICreateConnection, self).__init__(bluez.OCF_CREATE_CONN)
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
    def __init__(self, conn_handle, reason):
        super(HCIDisconnect, self).__init__(bluez.OCF_DISCONNECT)
        self.conn_handle = conn_handle
        self.reason = reason

    def pack_param(self):
        return ''.join((htole16(self.conn_handle), htole8(self.reason)))
 
class HCIAcceptConnectionRequest(HCILinkControlCommand):
    def __init__(self, bd_addr, role):
        super(HCIAcceptConnectionRequest, self).__init__(bluez.OCF_ACCEPT_CONN_REQ)
        self.bd_addr = bd_addr
        self.role = role

    def pack_param(self):
        return ''.join((self.bd_addr, htole8(self.role)))

class HCIControllerCommand(HCICommand):
    def __init__(self, ocf):
        super(HCIControllerCommand, self).__init__(bluez.OGF_HOST_CTL, ocf)

class HCISetEventMask(HCIControllerCommand):
    def __init__(self, event_mask):
        super(HCISetEventMask, self).__init__(bluez.OCF_SET_EVENT_MASK)
        self.event_mask = event_mask

    def pack_param(self):
        return htole64(self.event_mask)

class HCIReset(HCIControllerCommand):
    def __init__(self):
        super(HCIReset, self).__init__(bluez.OCF_RESET)

class HCIReadScanEnable(HCIControllerCommand):
    def __init__(self):
        super(HCIReadScanEnable, self).__init__(bluez.OCF_READ_SCAN_ENABLE)

class HCIWriteScanEnable(HCIControllerCommand):
    def __init__(self, scan_enable):
        super(HCIWriteScanEnable, self).__init__(bluez.OCF_WRITE_SCAN_ENABLE)
        self.scan_enable = scan_enable
        print bluez.OCF_WRITE_SCAN_ENABLE

    def pack_param(self):
        return htole8(self.scan_enable)

class HCIWritePageScanActivity(HCIControllerCommand):
    def __init__(self, page_scan_intvl, page_scan_window):
        super(HCIWritePageScanActivity, self).__init__(bluez.OCF_WRITE_PAGE_ACTIVITY)
        self.page_scan_intvl = page_scan_intvl
        self.page_scan_window = page_scan_window

    def pack_param(self):
        return ''.join(
                (htole16(self.page_scan_intvl),
                    htole16(self.page_scan_window)))

class HCIReadInquiryMode(HCIControllerCommand):
    def __init__(self):
        super(HCIReadInquiryMode, self).__init__(bluez.OCF_READ_INQUIRY_MODE)

class HCIWriteInquiryMode(HCIControllerCommand):
    def __init__(self, mode):
        super(HCIWriteInquiryMode, self).__init__(bluez.OCF_WRITE_INQUIRY_MODE)
        self.mode = mode

    def pack_param(self):
        return htole8(self.mode)


class HCIInfoParamCommand(HCICommand):
    def __init__(self, ocf):
        super(HCIInfoParamCommand, self).__init__(bluez.OGF_INFO_PARAM, ocf)

class HCIReadBDAddr(HCIInfoParamCommand):
    def __init__(self):
        super(HCIReadBDAddr, self).__init__(bluez.OCF_READ_BD_ADDR)


class HCILEControllerCommand(HCICommand):
    def __init__(self, ocf):
        super(HCILEControllerCommand, self).__init__(bluez.OGF_LE_CTL, ocf)

class HCILESetEventMask(HCILEControllerCommand):
    def __init__(self, le_evt_mask):
        super(HCILESetEventMask, self).__init__(bluez.OCF_LE_SET_EVENT_MASK)
        self.le_evt_mask = le_evt_mask

    def pack_param(self):
        return htole64(self.le_evt_mask)

class HCILEReadBufferSize(HCILEControllerCommand):
    def __init__(self):
        super(HCILEReadBufferSize, self).__init__(bluez.OCF_LE_READ_BUFFER_SIZE)

class HCILESetAdvertisingParameters(HCILEControllerCommand):
    def __init__(self, adv_intvl_min, adv_intvl_max, adv_type, own_addr_type, direct_addr_type, direct_addr, adv_channel_map, adv_filter_policy):
        super(HCILESetAdvertisingParameters, self).__init__(
                bluez.OCF_LE_SET_ADVERTISING_PARAMETERS)
        self.adv_intvl_min = adv_intvl_min
        self.adv_intvl_max = adv_intvl_max
        self.adv_type = adv_type
        self.own_addr_type = own_addr_type
        self.direct_addr_type = direct_addr_type
        self.direct_addr = direct_addr
        self.adv_channel_map = adv_channel_map
        self.adv_filter_policy = adv_filter_policy

    def pack_param(self):
        return ''.join(
                (htole16(self.adv_intvl_min),
                    htole16(self.adv_intvl_max),
                    htole8(self.adv_type),
                    htole8(self.own_addr_type),
                    htole8(self.direct_addr_type),
                    self.direct_addr,
                    htole8(self.adv_channel_map),
                    htole8(self.adv_filter_policy)))

class HCILESetAdvertisingData(HCILEControllerCommand):
    def __init__(self, adv_data):
        super(HCILESetAdvertisingData, self).__init__(
                bluez.OCF_LE_SET_ADVERTISING_DATA)
        self.adv_data_len = len(adv_data)
        self.adv_data = ''.join((adv_data, '\x00'*(31 - self.adv_data_len)))

    def pack_param(self):
        return ''.join((htole8(self.adv_data_len), self.adv_data))

class HCILESetAdvertiseEnable(HCILEControllerCommand):
    def __init__(self, adv_enable):
        super(HCILESetAdvertiseEnable, self).__init__(
                bluez.OCF_LE_SET_ADVERTISE_ENABLE)
        self.adv_enable = adv_enable

    def pack_param(self):
        return htole8(self.adv_enable)

class HCILECreateConnection(HCILEControllerCommand):
    def __init__(self, scan_intvl, scan_win, init_filter_policy, peer_addr_type, peer_addr, own_addr_type, conn_intvl_min, conn_intvl_max, conn_latency, supv_timeout, min_ce_len, max_ce_len):
        super(HCILECreateConnection, self).__init__(bluez.OCF_LE_CREATE_CONN)
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
        return ''.join(
                (htole16(self.scan_intvl),
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

class HCILECreateConnectionCancel(HCILEControllerCommand):
    def __init__(self):
        super(HCILECreateConnectionCancel, self).__init__(bluez.OCF_LE_CREATE_CONN_CANCEL)

class HCILEReadWhiteListSize(HCILEControllerCommand):
    def __init__(self):
        super(HCILEReadWhiteListSize, self).__init__(
                bluez.OCF_LE_READ_WHITE_LIST_SIZE)

class HCILEClearWhiteList(HCILEControllerCommand):
    def __init__(self):
        super(HCILEClearWhiteList, self).__init__(bluez.OCF_LE_CLEAR_WHITE_LIST)

class HCILEAddDeviceToWhiteList(HCILEControllerCommand):
    def __init__(self, addr_type, addr):
        super(HCILEAddDeviceToWhiteList, self).__init__(
                bluez.OCF_LE_ADD_DEVICE_TO_WHITE_LIST)
        self.addr_type = addr_type
        self.addr = addr

    def pack_param(self):
        return ''.join((htole8(self.addr_type), self.addr))

class HCILERemoveDeviceFromWhiteList(HCILEControllerCommand):
    def __init__(self, addr_type, addr):
        super(HCILERemoveDeviceFromWhiteList, self).__init__(
                bluez.OCF_LE_REMOVE_DEVICE_FROM_WHITE_LIST)
        self.addr_type = addr_type
        self.addr = addr

    def pack_param(self):
        return ''.join((htole8(self.addr_type), self.addr))

class HCILESetDataLength(HCILEControllerCommand):
    def __init__(self, conn_handle, tx_octets, tx_time):
        super(HCILESetDataLength, self).__init__(bluez.OCF_LE_SET_DATA_LEN)
        self.conn_handle = conn_handle
        self.tx_octets = tx_octets
        self.tx_time = tx_time

    def pack_param(self):
        return ''.join((htole16(self.conn_handle),
            htole16(self.tx_octets),
            htole16(self.tx_time)))
