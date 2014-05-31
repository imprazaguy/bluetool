"""HCI ACL data and SCO data.
"""
from .utils import letoh16

class HCIACLData(object):
    def __init__(self, handle):
        self.conn_handle = handle

    @staticmethod
    def get_pkt_size(buf, offset=0):
        return 4 + letoh16(buf, offset + 2)

class HCISCOData(object):
    def __init__(self, handle):
        self.conn_handle = handle

    @staticmethod
    def get_pkt_size(buf, offset=0):
        return 3 + ord(buf[offset + 2])
