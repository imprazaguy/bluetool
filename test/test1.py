# performs a simple device inquiry, followed by a remote name request of each
# discovered device

from bluetool.command import *
from bluetool.core import *
from bluetool.event import *
import sys
import struct
import os
import bluetooth._bluetooth as bluez

class InquiryRSSIWorker(HCIWorker):
    def __init__(self, sock):
        super(InquiryRSSIWorker, self).__init__(sock)

    def read_inquiry_mode(self):
        cmd_pkt = HCIReadInquiryMode()
        worker.send_hci_cmd(cmd_pkt)
        evt = worker.recv_hci_evt(worker.get_hci_filter(
            event=bluez.EVT_CMD_COMPLETE, opcode=cmd_pkt.opcode))
        if evt.status != 0:
            return -1
        return evt.inquiry_mode

    def write_inquiry_mode(self, mode):
        cmd_pkt = HCIWriteInquiryMode(mode)
        worker.send_hci_cmd(cmd_pkt)
        evt = worker.recv_hci_evt(worker.get_hci_filter(
            event=bluez.EVT_CMD_COMPLETE, opcode=cmd_pkt.opcode))
        if evt.status != 0:
            return -1
        return 0

    def inquiry_with_rssi(self):
        self.set_hci_filter(self.get_hci_filter(event='all'))

        cmd_pkt = HCIInquiry(0x9e8b33, 4, 255)
        worker.send_hci_cmd(cmd_pkt)

        results = []
        done = False
        while not done:
            pkt = self.sock.recv(255)
            ptype, event, plen = struct.unpack("BBB", pkt[:3])
            if event == bluez.EVT_INQUIRY_RESULT_WITH_RSSI:
                pkt = pkt[3:]
                nrsp = struct.unpack("B", pkt[0])[0]
                for i in range(nrsp):
                    addr = bluez.ba2str( pkt[1+6*i:1+6*i+6] )
                    rssi = struct.unpack("b", pkt[1+13*nrsp+i])[0]
                    results.append( ( addr, rssi ) )
                    print "[%s] RSSI: [%d]" % (addr, rssi)
            elif event == bluez.EVT_INQUIRY_COMPLETE:
                done = True
            elif event == bluez.EVT_CMD_STATUS:
                status, ncmd, opcode = struct.unpack("BBH", pkt[3:7])
                if status != 0:
                    print "uh oh..."
                    printpacket(pkt[3:7])
                    done = True
            else:
                print "unrecognized packet type 0x%02x" % ptype


    def run(self):
        mode = self.read_inquiry_mode()
        print "current inquiry mode is {}".format(mode)

        if mode == mode:
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
    dev_id = 0
    try:
        sock = bluez.hci_open_dev(dev_id)
    except:
        print "error accessing bluetooth device..."
        sys.exit(1)

    worker = InquiryRSSIWorker(sock)
    worker.run()

