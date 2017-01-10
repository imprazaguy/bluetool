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

class HCIEventNotImplementedError(HCIError):
    def __init__(self, evt_code):
        self.evt_code = evt_code
        super(HCIEventNotImplementedError, self).__init__(
                '{}: code: 0x{:02X}'.format(self.__class__.__name__, evt_code))

class HCICommandCompleteEventNotImplementedError(HCIError):
    def __init__(self, opcode):
        self.opcode = opcode
        super(HCICommandCompleteEventNotImplementedError, self).__init__(
                '{}: opcode: 0x{:04X}'.format(self.__class__.__name__, opcode))

class HCILEEventNotImplementedError(HCIError):
    def __init__(self, subevt_code):
        self.subevt_code = subevt_code
        super(HCILEEventNotImplementedError, self).__init__(
                '{}: subevt_code: 0x{:02X}'.format(self.__class__.__name__, subevt_code))

class HCITimeoutError(HCIError):
    def __init__(self):
        super(HCITimeoutError, self).__init__()

class HCICommandError(HCIError):
    def __init__(self, hci_evt):
        super(HCICommandError, self).__init__(
                '{} failure: opcode: 0x{:04x}, status: 0x{:02x}'.format(
                    hci_evt.__class__.__name__, hci_evt.cmd_opcode,
                    hci_evt.status))


class HCIInvalidCommandParametersError(HCIError):
    def __init__(self, hci_cmd):
        super(HCIInvalidCommandParametersError, self).__init__(
            '{} failure: invalid command parameters'.format(
                hci_cmd.__class__.__name__))


class TestError(Error):
    def __init__(self, msg):
        super(TestError, self).__init__(msg)
