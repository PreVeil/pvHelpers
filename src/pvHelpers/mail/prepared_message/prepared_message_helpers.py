from pvHelpers.crypto import SYMM_KEY_PROTOCOL_VERSION
from pvHelpers.crypto.utils import CryptoException
from pvHelpers.utils import b64enc, utf8Encode

FILE_BLOCK_SIZE = 2 * 1024 * 1024 # max 2MB block size

#########################################
######### Factory Common Mixins #########
#########################################
class PreparedMessageHelpers(object):
    def _encrypt(self, data, is_text = False):
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

    def _prepareBody(self, body):
        blocks, totalsize = self._encryptBlock(body)
        for block in blocks:
            self.uploads[block["cipherhash"]] = {
                "data": block["ciphertext"],
                "key_version":  self.recipient.public_user_key.key_version,
                "wrapped_key": self.sealed_opaque_key
            }

        encrypted_snippet = self._encrypt(self.email.snippet(), is_text=True)
        self.email.body.block_ids = [unicode(block["cipherhash"]) for block in blocks]
        self.body = {
            "snippet": encrypted_snippet["ciphertext"],
            "block_ids": self.email.body.block_ids,
            "size": totalsize
        }

    def _prepareAttachments(self, attachments):
        for attachment in attachments:
            blocks, totalsize = self._encryptBlock(attachment.content.content)
            encrypted_name = self._encrypt(attachment.metadata.filename, is_text=True)
            encrypted_name = encrypted_name["ciphertext"]

            for block in blocks:
                self.uploads[block["cipherhash"]] = {
                    "data": block["ciphertext"],
                    "key_version":  self.recipient.public_user_key.key_version,
                    "wrapped_key": self.sealed_opaque_key
                }
            attachment.content.block_ids = [unicode(block["cipherhash"]) for block in blocks]
            self.attachments.append({
                "block_ids": attachment.content.block_ids,
                "size": totalsize,
                "name": encrypted_name,
                "metadata": {
                    "content_type": attachment.metadata.content_type,
                    "content_id": attachment.metadata.content_id,
                    "content_disposition": attachment.metadata.content_disposition
                }
            })

    def _encryptBlock(self, data):
        # break the message up into chunks of at most FILE_BLOCK_SIZE
        chunks = [data[i:i+FILE_BLOCK_SIZE] for i in xrange(0, len(data), FILE_BLOCK_SIZE)]
        size = 0
        blocks = []
        for block in chunks:
            encrypted_block = self._encrypt(block)
            size += len(block)
            blocks.append(encrypted_block)

        return blocks, size

    def toDict(self):
        return {
            "message_id": self.email.message_id,
            "in_reply_to": self.email.in_reply_to,
            "references": self.email.references,
            "flags": self.email.flags, # should sender enforce flags?!,
            "protocol_version": self.email.protocol_version,
            "private_metadata": self.private_metadata,
            "attachments": self.attachments,
            "body": self.body
        }


class PreparedMessageError(Exception):
    def __init__(self, exception=u""):
        super(PreparedMessageError, self).__init__(exception)
