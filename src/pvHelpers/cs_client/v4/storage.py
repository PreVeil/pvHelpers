import types

import pvHelpers as H

STORAGE_REQUEST_TIMEOUT = 120

class StorageV4(object):
    @H.params(object, H.LocalUser, H.PreparedMessageBase)
    def uploadEmailBlocks(self, user, prepared_message):
        for block_id, block in prepared_message.uploads.iteritems():
            url, raw_body, headers = self.prepareSignedRequest(
                user,
                "/storage/{}/blocks/{}".format(
                    prepared_message.recipient.mail_cid, block_id),
                "PUT", block
            )
            resp = self.put(url, headers, raw_body,
                            timeout=STORAGE_REQUEST_TIMEOUT)
            resp.raise_for_status()

    @H.params(object, {H.LocalUser, H.UserDBNode}, [unicode], {types.NoneType, unicode})
    def downloadBlocks(self, user, block_ids, collection_id=None):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/storage/{}/blocks".format(
                user.mail_cid if not collection_id else collection_id),
            "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
                        "block_ids": H.jdumps(block_ids)}, timeout=STORAGE_REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data.get("blocks"), list):
            raise H.ServerResponseError("Response bad type `blocks`")

        canonical_str = u"".join(sorted(block_ids)).upper()
        blocks = {}
        for b in data.get("blocks"):
            block_id = b.get("block_id")
            if block_id is None:
                raise H.ServerResponseError("Response bad type `block_id`")

            b64enc_block = b.get("data")
            if not b64enc_block:
                raise H.ServerResponseError("Missing block content")

            raw_cipher = H.b64dec(b64enc_block)
            content_hash = H.HexEncode(H.Sha256Sum(raw_cipher))
            if content_hash.upper() not in canonical_str:
                raise H.ServerResponseError(
                    "Returned block content hash does not match any requested block_ids")

            blocks[block_id] = b

        return blocks
