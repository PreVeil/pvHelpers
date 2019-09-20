import pvHelpers as H

from .prepared_message_base import PreparedMessageBase
from .prepared_message_helpers import (PreparedMessageError,
                                       PreparedMessageHelpers)
from .prepared_message_v1 import PreparedMessageV1


class PreparedMessageV2(PreparedMessageHelpers, PreparedMessageBase):
    """PV2 is complying prepared message for Email Entity PV2"""
    PROTOCOL_VERSION = H.PROTOCOL_VERSION.V2

    def __init__(self, sender, email, recipient):
        super(PreparedMessageV2, self).__init__(sender, email, recipient)

        if not isinstance(email, H.EmailV2):
            raise PreparedMessageError(u"PreparedMessageV2.__init__: email must be of type H.EmailV2")

        self._prepareAttachments(self.email.attachments)
        self._prepareBody(self.email.body.content)

        status, signature = self._sign()
        if not status:
            raise PreparedMessageError(u"PreparedMessageV2.__init__: Failed to sign content")

        self.private_metadata["sender"] = self.sender.user_id
        self.private_metadata["subject"] = self.email.subject
        self.private_metadata["signature"] = signature
        self.private_metadata["signing_key_version"] = self.sender.user_key.key_version

        if self.recipient.user_id is self.sender.user_id:
            bccs = [bcc["user_id"] for bcc in self.email.bccs]
        elif self.recipient.user_id in [bcc["user_id"] for bcc in self.email.bccs] or self.recipient.user_id not in [recip["user_id"] for recip in self.email.tos + self.email.ccs]:
            bccs = [self.recipient.user_id]
        else:
            bccs = []

        self.private_metadata["bccs"] = bccs
        self.private_metadata["tos"] = [to["user_id"] for to in self.email.tos]
        self.private_metadata["ccs"] = [cc["user_id"] for cc in self.email.ccs]
        self.private_metadata["other_headers"] = self.email.other_headers

        encrypted_metadata = self._encrypt(H.jdumps(self.private_metadata), is_text=True)
        self.private_metadata = encrypted_metadata["ciphertext"]


    def _sign(self):
        status, canonical_msg_str = PreparedMessageV1.canonicalEncryptedString(self.uploads)
        if not status:
            H.g_log.error(u"PreparedMessageV2._sign: Failed to get canonical encrypted string")
            return False, None

        signature = H.b64enc(self.sender.user_key.signing_key.sign(H.utf8Encode(canonical_msg_str)))
        return True, signature
