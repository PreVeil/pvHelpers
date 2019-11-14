from pvHelpers.crypto import ASYMM_KEY_PROTOCOL_VERSION, SYMM_KEY_PROTOCOL_VERSION
from pvHelpers.crypto.utils import CryptoException
from pvHelpers.mail.email import PROTOCOL_VERSION
from pvHelpers.utils import b64enc, utf8Encode

FILE_BLOCK_SIZE = 2 * 1024 * 1024  # max 2MB block size


class PreparedMessageHelpers(object):
    """PreparedMessage entiry mixins"""

    def _encrypt(self, data, is_text=False):
        details = {}
        try:
            if is_text:
                if self.opaque_key.protocol_version == SYMM_KEY_PROTOCOL_VERSION.V1:
                    ciphertext = b64enc(self.opaque_key.encrypt(utf8Encode(data), details))
                else:
                    ciphertext = b64enc(self.opaque_key.encrypt(utf8Encode(data), details, is_text=True))
            else:
                ciphertext = b64enc(self.opaque_key.encrypt(data, details))
        except CryptoException as e:
            raise PreparedMessageError(e)

        return {
            "ciphertext": ciphertext,
            "cipherhash": details.get("sha256"),
            "length": details.get("length")
        }

    def wrapped_key_for(self, opaque_key, for_user):
        if for_user.public_user_key.public_key.protocol_version >= ASYMM_KEY_PROTOCOL_VERSION.V3:
            return b64enc(for_user.public_user_key.public_key.seal(opaque_key.serialize()))
        return b64enc(for_user.public_user_key.public_key.seal(opaque_key.serialize(), is_text=True))

    def _key_version(self, protocol_version):
        if protocol_version <= PROTOCOL_VERSION.V4:
            return self.recipient.public_user_key.key_version
        elif protocol_version >= PROTOCOL_VERSION.V5:
            return self.sender.public_user_key.key_version
        raise PreparedMessageError(u"Invalid protocol version {}".format(protocol_version))

    def _prepare_body(self, body, protocol_version):
        blocks, totalsize = self._encrypt_block(body)
        for block in blocks:
            self.uploads[block["cipherhash"]] = {
                "data": block["ciphertext"],
                "key_version":  self._key_version(protocol_version),
                "wrapped_key": self.sealed_opaque_key
            }

        if protocol_version <= PROTOCOL_VERSION.V4:
            snippet = self._encrypt(self.email.snippet(), is_text=True)[
                "ciphertext"]
        elif protocol_version >= PROTOCOL_VERSION.V5:
            snippet = self.email.snippet()
        self.email.body.block_ids = [unicode(block["cipherhash"]) for block in blocks]
        self.body = {
            "snippet": snippet,
            "block_ids": self.email.body.block_ids,
            "size": totalsize
        }

    def _prepare_attachments(self, attachments, protocol_version):
        for attachment in attachments:
            blocks, totalsize = self._encrypt_block(attachment.content.content)

            if protocol_version <= PROTOCOL_VERSION.V4:
                name = self._encrypt(
                    attachment.metadata.filename, is_text=True)["ciphertext"]
            elif protocol_version >= PROTOCOL_VERSION.V5:
                name = attachment.metadata.filename

            for block in blocks:
                self.uploads[block["cipherhash"]] = {
                    "data": block["ciphertext"],
                    "key_version":  self._key_version(protocol_version),
                    "wrapped_key": self.sealed_opaque_key
                }
            attachment.content.block_ids = [unicode(block["cipherhash"]) for block in blocks]
            self.attachments.append({
                "block_ids": attachment.content.block_ids,
                "size": totalsize,
                "name": name,
                "metadata": {
                    "content_type": attachment.metadata.content_type,
                    "content_id": attachment.metadata.content_id,
                    "content_disposition": attachment.metadata.content_disposition
                }
            })

    def _encrypt_block(self, data):
        # break the message up into chunks of at most FILE_BLOCK_SIZE
        chunks = [data[i:i+FILE_BLOCK_SIZE] for i in xrange(0, len(data), FILE_BLOCK_SIZE)]
        size = 0
        blocks = []
        for block in chunks:
            encrypted_block = self._encrypt(block)
            size += len(block)
            blocks.append(encrypted_block)

        return blocks, size

    def to_dict(self):
        return {
            "message_id": self.email.message_id,
            "in_reply_to": self.email.in_reply_to,
            "references": self.email.references,
            "flags": self.email.flags,  # should sender enforce flags?
            "protocol_version": self.protocol_version,
            "private_metadata": self.private_metadata,
            "attachments": self.attachments,
            "body": self.body
        }


class PreparedMessageError(Exception):
    def __init__(self, exception=u""):
        super(PreparedMessageError, self).__init__(exception)
