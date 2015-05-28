# performs a simple device inquiry, followed by a remote name request of each
# discovered device

import bluetool
from bluetool.command import *
from bluetool.core import *
from bluetool.event import *
import sys
import struct
import os
import bluetooth._bluetooth as bluez

class InquiryRSSIWorker(HCITask):
    def __init__(self, sock):
        super(InquiryRSSIWorker, self).__init__(sock)

    def read_inquiry_mode(self):
        cmd_pkt = HCIReadInquiryMode()
        evt = self.send_hci_cmd_wait_cmd_complt(cmd_pkt)
        if evt.status != 0:
            return -1
        return evt.inquiry_mode

    def write_inquiry_mode(self, mode):
        cmd_pkt = HCIWriteInquiryMode(mode)
        evt = self.send_hci_cmd_wait_cmd_complt(cmd_pkt)
        if evt.status != 0:
            return -1
        return 0

    def inquiry_with_rssi(self):
        cmd_pkt = HCIInquiry(0x9e8b33, 4, 255)
        self.send_hci_cmd(cmd_pkt)

        results = []
        done = False
        while not done:
            evt = self.recv_hci_evt()
            if evt.code == bluez.EVT_INQUIRY_RESULT_WITH_RSSI:
                for i in xrange(evt.num_responses):
                    addr = bluez.ba2str(evt.bd_addr[i])
                    rssi = evt.rssi[i]
                    results.append( ( addr, rssi ) )
                    print "[{}] RSSI: [{}]".format(addr, rssi)
            elif evt.code == bluez.EVT_INQUIRY_COMPLETE:
                done = True
            elif evt.code == bluez.EVT_CMD_STATUS:
                if evt.status != 0:
                    print "uh oh..."
                    done = True
            else:
                print "unrecognized event: {}".format(evt)


    def run(self):
        mode = self.read_inquiry_mode()
        print "current inquiry mode is {}".format(mode)

        if mode != 1:
            print "writing inquiry mode..."
            result = self.write_inquiry_mode(1)
            if result != 0:
                print "error while setting inquiry mode"

        self.inquiry_with_rssi()

def printpacket(pkt):
    for c in pkt:
        sys.stdout.write("%02x " % struct.unpack("B",c)[0])
    print 

if __name__ == "__main__":
    bluetool.log_to_stream()
    dev_id = 0
    try:
        hci_sock = HCISock(dev_id)
    except:
        print "error accessing bluetooth device..."
        sys.exit(1)

    worker = InquiryRSSIWorker(hci_sock)
    worker.run()

