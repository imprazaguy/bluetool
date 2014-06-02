# -*- coding: utf-8 -*-
"""HCI command
"""

import struct
import bluetooth._bluetooth as bluez


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

