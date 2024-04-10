class HFTPException(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ClientDisconnectedError(HFTPException):

    def __init__(self):
        message = "client disconnected unexpectedly"
        super().__init__(message)

class NewlineOutsideEOL(HFTPException):

    def __init__(self):
        super().__init__()

class InvalidCommand(HFTPException):

    def __init__(self, message):
        super().__init__(message)