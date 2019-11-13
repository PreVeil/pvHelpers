from .helpers import PROTOCOL_VERSION
from .v1 import EmailV1


class EmailV3(EmailV1):
    """Testing version: Protocol version 3 is identical to protocol version 1"""
    protocol_version = PROTOCOL_VERSION.V3

    def __init__(self, *args, **kwargs):
        super(EmailV3, self).__init__(*args, **kwargs)
