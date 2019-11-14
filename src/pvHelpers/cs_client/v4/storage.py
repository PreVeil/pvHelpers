import types

from pvHelpers.crypto.utils import HexEncode, Sha256Sum
from pvHelpers.mail import PreparedMessageBase
from pvHelpers.user import LocalUser
from pvHelpers.utils import b64dec, jdumps, params

from ..utils import ServerResponseError

STORAGE_REQUEST_TIMEOUT = 120


class StorageV4(object):
    # NOTEXX: needs fixing on consumers
    @params(object, LocalUser, unicode, PreparedMessageBase)
    def uploadEmailBlocks(self, user, collection_id, prepared_message):
        for block_id, block in prepared_message.uploads.iteritems():
            url, raw_body, headers = self.prepareSignedRequest(
                user,
                "/storage/{}/blocks/{}".format(collection_id, block_id),
                "PUT", block
            )
            resp = self.put(url, headers, raw_body,
                            timeout=STORAGE_REQUEST_TIMEOUT)
            resp.raise_for_status()

    @params(object, LocalUser, [unicode], {types.NoneType, unicode})
    def downloadBlocks(self, user, block_ids, collection_id=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/storage/{}/blocks".format(
                user.mail_cid if not collection_id else collection_id),
            "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
                        "block_ids": jdumps(block_ids)}, timeout=STORAGE_REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data.get("blocks"), list):
            raise ServerResponseError("Response bad type `blocks`")

        canonical_str = u"".join(sorted(block_ids)).upper()
        blocks = {}
        for b in data.get("blocks"):
            block_id = b.get("block_id")
            if block_id is None:
                raise ServerResponseError("Response bad type `block_id`")

            b64enc_block = b.get("data")
            if not b64enc_block:
                raise ServerResponseError("Missing block content")

            raw_cipher = b64dec(b64enc_block)
            content_hash = HexEncode(Sha256Sum(raw_cipher))
            if content_hash.upper() not in canonical_str:
                raise ServerResponseError(
                    "Returned block content hash does not match any requested block_ids")

            blocks[block_id] = b

        return blocks
