# TP/CCO/BV-11-C [LE Write Suggested Default Data Length Command]
#
# Verify that the IUT correctly handles the LE Write Suggested Default Data
# Length Command

import bluetool
from bluetool.core import HCICoordinator, HCIWorker, LEHelper
import bluetool.command as btcmd
import bluetool.error as bterr


class IUT(HCIWorker):
    def main(self):
        helper = LEHelper(self.sock)

        succeeded = False

        try:
            helper.reset()
            cmd = btcmd.HCILEWriteSuggestedDefaultDataLength(251, (251+14)*8)
            helper.send_hci_cmd_wait_cmd_complt_check_status(cmd)
            cmd = btcmd.HCILEReadSuggestedDefaultDataLength()
            helper.send_hci_cmd_wait_cmd_complt_check_status(cmd)
            succeeded = True
        except bterr.Error as err:
            self.log.warning(str(err), exc_info=True)

        self.send(succeeded)


class TestManager(HCICoordinator):
    def main(self):
        succeeded = self.iut.recv()
        if succeeded:
            return 0
        else:
            return 1


bluetest = {
    'coordinator': TestManager,
    'worker': [
        ('iut', IUT)
    ]
}


if __name__ == "__main__":
    bluetool.log_to_stream()
    bluetool.run_config(bluetest, [0])
