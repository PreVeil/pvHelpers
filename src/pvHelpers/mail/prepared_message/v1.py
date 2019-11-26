from flanker import mime
from pvHelpers.crypto.utils import hex_encode, sha_256_sum
from pvHelpers.logger import g_log
from pvHelpers.mail.email import EmailV1, PROTOCOL_VERSION
from pvHelpers.utils import b64enc, jdumps, utf8Encode

from .base import PreparedMessageBase
from .helpers import PreparedMessageError, PreparedMessageHelpers


class PreparedMessageV1(PreparedMessageHelpers, PreparedMessageBase):
    """PV1 is complying prepared message for Email Entity PV1"""
    PROTOCOL_VERSION = PROTOCOL_VERSION.V1

    def __init__(self, sender, email, recipient):
        super(PreparedMessageV1, self).__init__(sender, email)

        self.recipient = recipient
        self.sealed_opaque_key = None
        self.sealed_opaque_key = self.wrapped_key_for(self.opaque_key, self.recipient)

        self._prepare_attachments(self.email.attachments, self.protocol_version)

        try:
            body_mime = mime.create.from_string(self.email.body.content)
        except mime.MimeError as e:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: flanker exception: {}".format(e))

        # This replacement due PROTOCOL_VERSION 1 body serialization which uses
        # block_ids of attachments for referencing dummy nodes, while locally we use
        # attachment hash for referencing so that attachment separation can be independent
        # of any encryption or server storage upload
        status, body_mime = EmailV1.replaceDummyReferences(
            body_mime, {
                hex_encode(sha_256_sum(att.content.content)): u",".join(att.content.block_ids)
                for att in self.email.attachments
            })

        if not status:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: Failed to replace dummy references")
        if self.recipient.user_id == self.sender.user_id:
            status, body_mime = EmailV1.setMIMEBcc(body_mime, self.email.bccs)
        else:
            if self.recipient.user_id in [bcc["user_id"] for bcc in self.email.bccs] or \
               self.recipient.user_id not in [recip["user_id"] for recip in self.email.tos + self.email.ccs]:
                status, body_mime = EmailV1.setMIMEBcc(
                    body_mime, [{"user_id": self.recipient.user_id, "display_name": self.recipient.display_name}])
            else:
                status, body_mime = EmailV1.setMIMEBcc(body_mime, [])

        if not status:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: Failed to modify Bccs")

        try:
            body = body_mime.to_string()
        except mime.MimeError as e:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: flanker exception: {}".format(e))

        self._prepare_body(body, self.protocol_version)

        status, signature = self._sign()
        if not status:
            raise PreparedMessageError(u"PreparedMessageV1.__init__: Failed to sign content")

        self.private_metadata["sender"] = self.sender.user_id
        self.private_metadata["subject"] = self.email.subject
        self.private_metadata["signature"] = signature
        self.private_metadata["signing_key_version"] = self.sender.user_key.key_version

        self.private_metadata["tos"] = self.email.tos
        self.private_metadata["ccs"] = self.email.ccs

        encrypted_metadata = self._encrypt(jdumps(self.private_metadata), is_text=True)
        self.private_metadata = encrypted_metadata["ciphertext"]

    def _sign(self):
        status, canonical_msg_str = PreparedMessageV1.canonical_encrypted_string(self.uploads)
        if not status:
            g_log.error(u"PreparedMessageV1._sign: Failed to get canonical encrypted string")
            return False, None

        signature = b64enc(self.sender.user_key.signing_key.sign(utf8Encode(canonical_msg_str)))
        return True, signature

    @staticmethod
    def canonical_encrypted_string(blocks):
        msg = ""
        for block_id in sorted(blocks):
            block = blocks[block_id]
            if not isinstance(block, dict):
                g_log.error(u"PreparedMessageV1.canonical_encrypted_string: block must be of type dict")
                return False, None

            x = block.get("data")
            if not isinstance(x, unicode):
                g_log.error(u"PreparedMessageV1.canonical_encrypted_string: block data must be of type unicode")
                return False, None
            msg += x

        return True, msg
