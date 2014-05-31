# -*- coding: utf-8 -*-
"""HCI command.
"""
import struct

from . import bluez


class HCICommand(object):
    """Base HCI command object."""

    def __init__(self, ogf, ocf):
        self.ogf = ogf
        self.ocf = ocf

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
        return 3 + ord(buf[offset + 2])

class HCIReadInquiryMode(HCICommand):
    def __init__(self):
        super(HCIReadInquiryMode, self).__init__(bluez.OGF_HOST_CTL,
                bluez.OCF_READ_INQUIRY_MODE)

class HCIWriteInquiryMode(HCICommand):
    param_fmt = struct.Struct('<B')

    def __init__(self, mode):
        super(HCIWriteInquiryMode, self).__init__(bluez.OGF_HOST_CTL,
                bluez.OCF_WRITE_INQUIRY_MODE)
        self.mode = mode

    def pack_param(self):
        return self.param_fmt.pack(self.mode)

class HCIInquiry(HCICommand):
    def __init__(self, lap, inquiry_len, num_responses):
        super(HCIInquiry, self).__init__(bluez.OGF_LINK_CTL, bluez.OCF_INQUIRY)
        self.lap = lap
        self.inquiry_len = inquiry_len
        self.num_responses = num_responses

    def pack_param(self):
        param = struct.pack('<I', self.lap)[:3]
        param += struct.pack('<BB', self.inquiry_len, self.num_responses)
        return param

class HCILEControllerCommand(HCICommand):
    def __init__(self, ocf):
        super(HCILEControllerCommand, self).__init__(bluz.OGF_LE_CTL, ocf)

class HCILESetAdvertisingParameters(HCILEControllerCommand):
    param_fmt = struct.Struct('<HHBBB6sBB')

    def __init__(self, adv_intvl_min, adv_intvl_max, adv_type, own_addr_type, direct_addr_type, direct_addr, adv_channel_map, adv_filter_policy):
        super(HCILESetAdvertisingParameter, self).__init__(
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
        return self.param_fmt.pack(self.adv_intvl_min, self.adv_intvl_max,
                self.adv_type, self.own_addr_type, self.direct_addr_type,
                self.direct_addr, self.adv_channel_map, self.adv_filter_policy)

class HCILESetAdvertisingData(HCILEControllerCommand):
    def __init__(self, adv_data_len, adv_data):
        super(HCILESetAdvertisingData, self).__init__(
                bluez.OCF_LE_SET_ADVERTISING_DATA)
        self.adv_data_len = adv_data_len
        self.adv_data = adv_data

    def pack_param(self):
        param = struct.pack('<B', self.adv_data_len)
        param += self.adv_data
        return param

class HCILESetAdvertiseEnable(HCILEControllerCommand):
    def __init__(self, adv_enable):
        super(HCILESetAdvertiseEnable, self).__init__(
                bluez.OCF_LE_SET_ADVERTISE_ENABLE)
        self.adv_enable = adv_enable
    def pack_param(self):
        return struct.pack('<B', self.adv_enable)

class HCILEReadWhiteListSize(HCILEControllerCommand):
    def __init__(self):
        super(HCILEReadWhiteListSize, self).__init__(
                bluez.OCF_LE_READ_WHITE_LIST_SIZE)

class HCILEClearWhiteList(HCILEControllerCommand):
    def __init__(self):
        super(HCILEClearWhiteList, self).__init__(bluez.OCF_LE_CLEAR_WHITE_LIST)

class HCILEAddDeviceToWhiteList(HCILEControllerCommand):
    param_fmt = struct.Struct('<B6s')

    def __init__(self, addr_type, addr):
        super(HCILEAddDeviceToWhiteList, self).__init__(
                bluez.OCF_LE_ADD_DEVICE_TO_WHITE_LIST)
        self.addr_type = addr_type
        self.addr = addr

    def pack_param(self):
        return self.param_fmt.pack(self.addr_type, self.addr)

class HCILERemoveDeviceFromWhiteList(HCILEControllerCommand):
    param_fmt = struct.Struct('<B6s')

    def __init__(self, addr_type, addr):
        super(HCILERemoveDeviceFromWhiteList, self).__init__(
                bluez.OCF_LE_REMOVE_DEVICE_FROM_WHITE_LIST)
        self.addr_type = addr_type
        self.addr = addr

    def pack_param(self):
        return self.param_fmt.pack(self.addr_type, self.addr)

class HCILECreateConnection(HCILEControllerCommand):
    param_fmt = struct.Struct('<HHBB6sBHHHHHH')

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
        return self.param_fmt.pack(self.scan_intvl, self.scan_win,
                self.init_filter_policy, self.peer_addr_type, self.peer_addr,
                self.own_addr_type, self.conn_intvl_min, self.conn_intvl_max,
                self.conn_latency, self.supv_timeout, self.min_ce_len,
                self.max_ce_len)
