import pvHelpers as H

from .prepared_message_v1 import PreparedMessageV1


class PreparedMessageV3(PreparedMessageV1):
    """PV3 is identical to PV1 as for email entity but has new signing method"""
    PROTOCOL_VERSION = H.PROTOCOL_VERSION.V3

    def __init__(self, sender, email, recipient):
        super(PreparedMessageV3, self).__init__(sender, email, recipient)

    def _sign(self):
        canonical_msg_str = PreparedMessageV3.canonicalEncryptedString(self.uploads)
        signature = H.b64enc(self.sender.user_key.signing_key.sign(H.utf8Encode(canonical_msg_str)))
        return True, signature

    @staticmethod
    def canonicalEncryptedString(blocks):
        return u"".join(sorted(blocks.keys()))
