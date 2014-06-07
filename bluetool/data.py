"""HCI ACL data and SCO data.
"""
from .error import HCIParseError
from .utils import letoh8, letoh16

class HCIACLData(object):
    def __init__(self):
        super(HCIACLData, self).__init__()

    @staticmethod
    def get_pkt_size(buf, offset=0):
        return 4 + letoh16(buf, offset + 2)

    @staticmethod
    def parse(buf, offset=0):
        avail_len = len(buf) - offset
        header = letoh16(buf, offset)
        offset += 2
        data_len = letoh16(buf, offset)
        offset += 2
        if avail_len < 4 + data_len:
            raise HCIParseError('not enough data to parse')

        obj = HCIACLData()
        obj.conn_handle = (header & 0x0fff)
        obj.pb_flag = ((header >> 12) & 0x3)
        obj.bc_flag = ((header >> 14) & 0x3)
        obj.data = buf[offset:offset+data_len]
        return obj

class HCISCOData(object):
    def __init__(self):
        super(HCISCOData, self).__init__()

    @staticmethod
    def get_pkt_size(buf, offset=0):
        return 3 + letoh8(buf, offset + 2)

    @staticmethod
    def parse(buf, offset=0):
        avail_len = len(buf) - offset
        header = letoh16(buf, offset)
        offset += 2
        data_len = letoh8(buf, offset)
        offset += 1
        if avail_len < 3 + data_len:
            raise HCIParseError('not enough data to parse')

        obj = HCISCOData()
        obj.conn_handle = (header & 0x0fff)
        obj.pkt_status_flag = ((header >> 12) & 0x3)
        obj.data = buf[offset:offset+data_len]
        return obj
