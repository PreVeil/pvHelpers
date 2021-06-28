import calendar
import time

from ..misc import utf8Encode, utf8Decode, jloads, b64dec, \
    MergeDicts, CaseInsensitiveSet, CaseInsensitiveDict, g_log
from ..crypto import Sha256Sum
from . import PROTOCOL_VERSION, EmailException

from pvHelpers.hook_decorators import WrapExceptions


# https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
def flatten_recipient_groups(recip_groups):
    return [
        u for sublist in map(lambda g: g["users"], recip_groups)
        for u in sublist
    ]


@WrapExceptions(EmailException, [KeyError])
def verifyServerMessage(message, verify_key):
    if message["protocol_version"] >= PROTOCOL_VERSION.V5:
        utf8_decode_pvm = utf8Decode(message["raw_private_metadata"])
        signature = b64dec(message["signature"])
        canonical_str = Sha256Sum(utf8Encode(utf8_decode_pvm))
    elif message["protocol_version"] == PROTOCOL_VERSION.V4:
        signature = b64dec(message["private_metadata"]["signature"])

        block_ids = []
        for attachment in message["attachments"]:
            for block in attachment["blocks"]:
                block_ids.append(block["id"])
        for block in message["body"]["blocks"]:
            block_ids.append(block["id"])
        canonical_str = utf8Encode(u"".join(sorted(block_ids)))
    else:
        # we don't verify signature for legacy protocol versions
        return True

    return verify_key.verify(canonical_str, signature)


@WrapExceptions(EmailException, [KeyError])
def getSender(message):
    if message["protocol_version"] >= PROTOCOL_VERSION.V5:
        return (message["private_metadata"]["sender"], int(message["sender_key_version"]))
    elif message["protocol_version"] == PROTOCOL_VERSION.V4:
        return (message["private_metadata"]["sender"], int(message["private_metadata"]["signing_key_version"]))
    else:
        raise ValueError("Unsupported protocol version {}".format(
            message["protocol_version"]))


@WrapExceptions(EmailException, [KeyError])
def decryptServerMessage(message, user_encryption_key, mail_decrypt_key):
    """
        message: Server's message object
        user_encryption_key: user's private key or api to decrypt using user's pv key
        mail_decrypt_key: symmetric key used to wrap email's props
    """
    if message["protocol_version"] >= PROTOCOL_VERSION.V5:
        raw_private_metadata = mail_decrypt_key.decrypt(
            b64dec(message["private_metadata"]))
        decrypted_private_metadata = jloads(utf8Decode(raw_private_metadata))

        bccs = []
        recipients = jloads(utf8Decode(user_encryption_key.unseal(
            b64dec(message["wrapped_recipients"]))))

        if message["wrapped_bccs"]:
            bccs = jloads(utf8Decode(user_encryption_key.unseal(
                b64dec(message["wrapped_bccs"]))))

        # verify the integrity of the wrapped_recipients and (optional) external sender against private metadata
        tos_groups = decrypted_private_metadata.get("tos_groups", [])
        ccs_groups = decrypted_private_metadata.get("ccs_groups", [])

        tos_groups_flatten = flatten_recipient_groups(tos_groups)
        ccs_groups_flatten = flatten_recipient_groups(ccs_groups)

        server_recips = CaseInsensitiveSet(map(lambda u: u["external_email"] if u.get("external_email") else u["user_id"], recipients))        
        pvm_recips = CaseInsensitiveSet(
                map(
                    lambda u: u["external_email"] if u.get("external_email") else u["user_id"], decrypted_private_metadata["ccs"] +
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
        return MergeDicts(message, {
            "body": decrypted_private_metadata["body"],
            "private_metadata": decrypted_private_metadata,
            "raw_private_metadata": raw_private_metadata,  # use for the signature verification
            "timestamp": calendar.timegm(time.strptime(message["timestamp"], "%Y-%m-%dT%H:%M:%S")),
            "attachments": decrypted_private_metadata["attachments"]
        })
    else:
        decrypted_private_metadata = jloads(utf8Decode(
            mail_decrypt_key.decrypt(b64dec(message["private_metadata"]))))

        return MergeDicts(message, {
            "body": MergeDicts(message["body"], {"snippet": utf8Decode(mail_decrypt_key.decrypt(b64dec(message["body"]["snippet"])))}),
            "private_metadata": decrypted_private_metadata,
            "timestamp": calendar.timegm(time.strptime(message["timestamp"], "%Y-%m-%dT%H:%M:%S")),
            "attachments": map(lambda att: MergeDicts(att, {"name": utf8Decode(mail_decrypt_key.decrypt(b64dec(att["name"])))}), message["attachments"])
        })


@WrapExceptions(EmailException, [KeyError])
def getWrappedKey(server_message):
    if server_message["protocol_version"] >= PROTOCOL_VERSION.V5:
        return server_message["recipient_key_version"], server_message["wrapped_key"]

    for block in server_message["body"]["blocks"]:
        return block["key_version"], block["wrapped_key"]
    for att in server_message["attachments"]:
        for block in att["blocks"]:
            return block["key_version"], block["wrapped_key"]

    raise EmailException(
        "No wrapped key provided in server message {}".format(server_message))
