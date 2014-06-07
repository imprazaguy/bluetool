class Error(Exception):
    def __init__(self, msg=''):
        super(Error, self).__init__()
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class HCIError(Error):
    def __init__(self, msg=''):
        super(HCIError, self).__init__(msg)
        self.msg = msg

class HCIParseError(HCIError):
    def __init__(self, msg):
        super(HCIParseError, self).__init__(msg)

class HCITimeoutError(HCIError):
    def __init__(self):
        super(HCITimeoutError, self).__init__()

class HCICommandError(HCIError):
    def __init__(self, hci_evt):
        super(HCIStatusError, self).__init__(
                '{} failure: opcode: 0x{:04x}, status: 0x{:02x}'.format(
                    hci_evt.__class__.__name__, hci_evt.cmd_opcode,
                    hci_evt.status))


class TestError(Error):
    def __init__(self, msg):
        super(TestError, self).__init__(msg)
