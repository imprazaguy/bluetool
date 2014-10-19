"""HCI ACL data and SCO data.
"""
from .error import HCIParseError
from .utils import letoh8, letoh16

class HCIACLData(object):
    def __init__(self, conn_handle, pb_flag=0x0, bc_flag=0x0, data=None):
        super(HCIACLData, self).__init__()
        self.conn_handle = conn_handle
        self.pb_flag = pb_flag
        self.bc_flag = bc_flag
        self.data = data

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

        conn_handle = (header & 0x0fff)
        pb_flag = ((header >> 12) & 0x3)
        bc_flag = ((header >> 14) & 0x3)
        if data_len > 0:
            data = buf[offset:offset+data_len]
        else:
            data = None
        return HCIACLData(conn_handle, pb_flag, bc_flag, data)

class HCISCOData(object):
    def __init__(self, conn_handle, pkt_status_flag=0x0, data=None):
        super(HCISCOData, self).__init__()
        self.conn_handle = conn_handle
        self.pkt_status_flag = pkt_status_flag
        self.data = data

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

        conn_handle = (header & 0x0fff)
        pkt_status_flag = ((header >> 12) & 0x3)
        if data_len > 0:
            data = buf[offset:offset+data_len]
        else:
            data = None
        return HCISCOData(conn_handle, pkt_status_flag, data)
