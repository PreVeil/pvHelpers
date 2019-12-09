import calendar
import time

from pvHelpers.crypto import sha_256_sum
from pvHelpers.logger import g_log
from pvHelpers.utils import (b64dec, CaseInsensitiveSet, jloads,
                             merge_dicts, utf8_decode, utf8_encode, WrapExceptions)

from .email import EmailException, PROTOCOL_VERSION


# https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
def flatten_recipient_groups(recip_groups):
    return [
        u for sublist in map(lambda g: g["users"], recip_groups)
        for u in sublist
    ]


@WrapExceptions(EmailException, [KeyError])
def verify_server_message(message, verify_key):
    if message["protocol_version"] >= PROTOCOL_VERSION.V5:
        utf8_decode_pvm = utf8_decode(message["raw_private_metadata"])
        signature = b64dec(message["signature"])
        canonical_str = sha_256_sum(utf8_encode(utf8_decode_pvm))
    elif message["protocol_version"] == PROTOCOL_VERSION.V4:
        signature = b64dec(message["private_metadata"]["signature"])

        block_ids = []
        for attachment in message["attachments"]:
            for block in attachment["blocks"]:
                block_ids.append(block["id"])
        for block in message["body"]["blocks"]:
            block_ids.append(block["id"])
        canonical_str = utf8_encode(u"".join(sorted(block_ids)))
    else:
        # we don't verify signature for legacy protocol versions
        return True

    return verify_key.verify(canonical_str, signature)


@WrapExceptions(EmailException, [KeyError])
def get_sender(message):
    if message["protocol_version"] >= PROTOCOL_VERSION.V5:
        return (message["private_metadata"]["sender"], int(message["sender_key_version"]))
    elif message["protocol_version"] == PROTOCOL_VERSION.V4:
        return (message["private_metadata"]["sender"], int(message["private_metadata"]["signing_key_version"]))
    else:
        raise ValueError("Unsupported protocol version {}".format(
            message["protocol_version"]))


@WrapExceptions(EmailException, [KeyError])
def decrypt_server_message(message, user_encryption_key, mail_decrypt_key):
    """
        message: Server's message object
        user_encryption_key: user's private key or api to decrypt using user's pv key
        mail_decrypt_key: symmetric key used to wrap email's props
    """
    if message["protocol_version"] >= PROTOCOL_VERSION.V5:
        raw_private_metadata = mail_decrypt_key.decrypt(
            b64dec(message["private_metadata"]))
        decrypted_private_metadata = jloads(utf8_decode(raw_private_metadata))

        bccs = []
        recipients = jloads(utf8_decode(user_encryption_key.unseal(
            b64dec(message["wrapped_recipients"]))))

        if message["wrapped_bccs"]:
            bccs = jloads(utf8_decode(user_encryption_key.unseal(
                b64dec(message["wrapped_bccs"]))))

        # verify the integrity of the wrapped_recipients against private metadata
        tos_groups = decrypted_private_metadata.get("tos_groups", [])
        ccs_groups = decrypted_private_metadata.get("ccs_groups", [])

        tos_groups_flatten = flatten_recipient_groups(tos_groups)
        ccs_groups_flatten = flatten_recipient_groups(ccs_groups)

        server_recips = CaseInsensitiveSet(map(lambda u: u["user_id"], recipients))
        pvm_recips = CaseInsensitiveSet(
                map(
                    lambda u: u["user_id"], decrypted_private_metadata["ccs"] +
                    decrypted_private_metadata["tos"] + tos_groups_flatten +
                    ccs_groups_flatten
                )
            )
        if server_recips != pvm_recips:
            g_log.debug("pvm recips={}".format(list(pvm_recips)))
            g_log.debug("decrypted server recips={}".format(list(server_recips)))
            raise EmailException(u"Server wrapped recipients don't match those of tos + ccs in private metadata")

        # combine group alias into tos and ccs for display purpose
        for tos_group in tos_groups:
            decrypted_private_metadata["tos"].append({
                "user_id": tos_group["alias"],
                "members": tos_group["users"],
                "key_version": None
            })

        for ccs_group in ccs_groups:
            decrypted_private_metadata["ccs"].append({
                "user_id": ccs_group["alias"],
                "members": ccs_group["users"],
                "key_version": None
            })

        decrypted_private_metadata["tos_groups"] = tos_groups_flatten
        decrypted_private_metadata["ccs_groups"] = ccs_groups_flatten

        decrypted_private_metadata["bccs"] = bccs
        return merge_dicts(message, {
            "body": decrypted_private_metadata["body"],
            "private_metadata": decrypted_private_metadata,
            "raw_private_metadata": raw_private_metadata,  # use for the signature verification
            "timestamp": calendar.timegm(time.strptime(message["timestamp"], "%Y-%m-%dT%H:%M:%S")),
            "attachments": decrypted_private_metadata["attachments"]
        })
    else:
        decrypted_private_metadata = jloads(utf8_decode(
            mail_decrypt_key.decrypt(b64dec(message["private_metadata"]))))

        return merge_dicts(message, {
            "body": merge_dicts(
                message["body"],
                {"snippet": utf8_decode(mail_decrypt_key.decrypt(b64dec(message["body"]["snippet"])))}),
            "private_metadata": decrypted_private_metadata,
            "timestamp": calendar.timegm(time.strptime(message["timestamp"], "%Y-%m-%dT%H:%M:%S")),
            "attachments": map(
                lambda att: merge_dicts(att, {"name": utf8_decode(mail_decrypt_key.decrypt(b64dec(att["name"])))}),
                message["attachments"])
        })


@WrapExceptions(EmailException, [KeyError])
def get_wrapped_key(server_message):
    if server_message["protocol_version"] >= PROTOCOL_VERSION.V5:
        return server_message["recipient_key_version"], server_message["wrapped_key"]

    for block in server_message["body"]["blocks"]:
        return block["key_version"], block["wrapped_key"]
    for att in server_message["attachments"]:
        for block in att["blocks"]:
            return block["key_version"], block["wrapped_key"]

    raise EmailException("No wrapped key provided in server message {}".format(server_message))
