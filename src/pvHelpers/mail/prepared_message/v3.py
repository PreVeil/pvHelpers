
from pvHelpers.mail.email import PROTOCOL_VERSION
from pvHelpers.utils import b64enc, utf8Encode

from .v1 import PreparedMessageV1


class PreparedMessageV3(PreparedMessageV1):
    """PV3 is identical to PV1 as for email entity but has new signing method"""
    PROTOCOL_VERSION = PROTOCOL_VERSION.V3

    def __init__(self, sender, email, recipient):
        super(PreparedMessageV3, self).__init__(sender, email, recipient)

    def _sign(self):
        canonical_msg_str = PreparedMessageV3.canonicalEncryptedString(self.uploads)
        signature = b64enc(self.sender.user_key.signing_key.sign(utf8Encode(canonical_msg_str)))
        return True, signature

    @staticmethod
    def canonicalEncryptedString(blocks):
        return u"".join(sorted(blocks.keys()))
