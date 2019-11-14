from .helpers import PROTOCOL_VERSION
from .v4 import EmailV4


class EmailV5(EmailV4):
    """
    Production version: Email version 5 is identical to that
    of version 4 Just for optic with the prepare_message V5
    """
    protocol_version = PROTOCOL_VERSION.V5

    def __init__(self, *args, **kwargs):
        super(EmailV5, self).__init__(*args, **kwargs)
