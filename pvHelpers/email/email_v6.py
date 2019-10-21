from .email_v4 import EmailV4
from .email_helpers import PROTOCOL_VERSION


class EmailV6(EmailV4):
    """Production version: Email version 6 is identical to email version 4
        Just for optic with the prepare_message V6
    """
    protocol_version = PROTOCOL_VERSION.V6

    def __init__(self, *args, **kwargs):
        super(EmailV6, self).__init__(*args, **kwargs)
