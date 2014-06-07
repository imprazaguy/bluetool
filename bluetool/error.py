class HCIError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class HCIParseError(HCIError):
    def __init__(self, msg):
        super(HCIParseError, self).__init__(msg)
