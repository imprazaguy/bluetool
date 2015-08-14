# Test LE ACL data transmission from master to slave.

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, HCIWorkerProxy, HCITask, LEHelper
from bluetool.bluez import ba2str
from bluetool.error import HCICommandError, TestError, HCITimeoutError
import bluetool.bluez as bluez
import bluetool.command as btcmd
import bluetool.event as btevt
from bluetool.data import HCIACLData
from bluetool.utils import bytes2str, htole16

CONN_TIMEOUT_MS = 10000

class LEMaster(HCIWorker):
    def __init__(self, hci_sock, coord, pipe):
        super(LEMaster, self).__init__(hci_sock, coord, pipe)

    def main(self):
        helper = LEHelper(self.sock)

        try:
            helper.reset()
            cmd = btcmd.HCILEReadSuggestedDefaultDataLength()
            helper.send_hci_cmd_wait_cmd_complt_check_status(cmd)
        except HCICommandError as err:
            self.log.warning('cannot reset', exc_info=True)
            return

class LETester(HCICoordinator):
    def __init__(self):
        super(LETester, self).__init__()
        self.worker.append(HCIWorkerProxy(0, self, LEMaster))

    def main(self):
        pass

if __name__ == "__main__":
    bluetool.log_to_stream()
    tester = LETester()
    tester.run()

