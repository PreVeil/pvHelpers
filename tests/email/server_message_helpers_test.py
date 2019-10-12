# vim: set fileencoding=utf-8 :
import pytest

import random

from pvHelpers import (EmailFactory, randUnicode, decryptServerMessage, b64enc,
                       verifyServerMessage, getSender, getWrappedKey,
                       flatten_recipient_groups, PROTOCOL_VERSION)
import pvHelpers as H

from server_message_mock import (MockServerMessageV5, MockPrivateMetadataV5,
                                 recipient, MockPrivateMetadataV6,
                                 MockServerMessageV6)


def _verify_recipients(email, pvm):
    if pvm.protocol_version == PROTOCOL_VERSION.V5:
        assert H.CaseInsensitiveSet(
            map(lambda u: u["user_id"], email.tos)) == H.CaseInsensitiveSet(
                map(lambda u: u["user_id"], pvm.tos))
        assert H.CaseInsensitiveSet(
            map(lambda u: u["user_id"], email.ccs)) == H.CaseInsensitiveSet(
                map(lambda u: u["user_id"], pvm.ccs))
    elif pvm.protocol_version == PROTOCOL_VERSION.V6:
        assert H.CaseInsensitiveSet(
            map(lambda u: u["user_id"], email.tos)) == H.CaseInsensitiveSet(
                map(lambda u: u["user_id"], pvm.tos) +
                map(lambda u: u["alias"], pvm.tos_groups))
        assert H.CaseInsensitiveSet(
            map(lambda u: u["user_id"], email.ccs)) == H.CaseInsensitiveSet(
                map(lambda u: u["user_id"], pvm.ccs) +
                map(lambda u: u["alias"], pvm.ccs_groups))
    else:
        raise ValueError("unsupported protocol version {}".format(pvm.protocol_version))


def _verifyEmail(email, pvm, msg):
    assert email.sender["user_id"] == pvm.sender
    assert email.subject == pvm.subject
    _verify_recipients(email, pvm)
    assert email.snippet() == pvm.body["snippet"]
    assert email.body.size == pvm.body["size"]
    assert email.body.block_ids == pvm.body["block_ids"]

    assert email.server_attr.server_id == msg.id
    assert email.server_attr.thread_id == msg.thread_id
    assert email.server_attr.revision_id == msg.rev_id
    assert email.server_attr.version == msg.version
    assert email.server_attr.uid == msg.uid
    assert email.server_attr.expunged == msg.is_deleted
    assert email.server_attr.mailbox_server_id == msg.mailbox_id

    # TODO: verify timestamp convertion


def test_server_message_parser_V6():
    sender_key_version = random.randint(0, 100)
    recipient_key_version = random.randint(0, 100)
    sender_user_key = H.PVKeyFactory.newUserKey(key_version=sender_key_version)
    sender = H.UserData(
        randUnicode(6), randUnicode(6), randUnicode(5),
        [sender_user_key.public_user_key], None)
    pvm = MockPrivateMetadataV6(sender=sender.user_id, user_key=sender_user_key)
    signature, encrypted_pvm = pvm.signAndEncrypt()

    wrapped_key = b64enc(
        pvm.user_key.public_user_key.public_key.seal(pvm.symm_key.serialize()))

    tos_groups_flatten = flatten_recipient_groups(pvm.tos_groups)
    ccs_groups_flatten = flatten_recipient_groups(pvm.ccs_groups)
    wrapped_recipients = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            H.utf8Encode(H.jdumps(pvm.tos + pvm.ccs + tos_groups_flatten + ccs_groups_flatten))))

    msg = MockServerMessageV6(encrypted_pvm, signature, sender_key_version,
                              recipient_key_version, wrapped_key,
                              wrapped_recipients)

    decrypted_msg = decryptServerMessage(msg.toDict(),
                                         pvm.user_key.encryption_key,
                                         pvm.symm_key)
    assert verifyServerMessage(decrypted_msg,
                               sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid

    email = EmailFactory.fromServerMessage(sender.user_id, decrypted_msg, wrapped_key, recipient_key_version, None)
    assert email.server_attr.collection_id == sender.mail_cid
    _verifyEmail(email, pvm, msg)

    # sender can see all bccs
    bccs = [recipient() for _ in range(3)]
    msg.wrapped_bccs = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            H.utf8Encode(H.jdumps(bccs))))
    decrypted_msg = decryptServerMessage(
        msg.toDict(), pvm.user_key.encryption_key, pvm.symm_key)
    assert verifyServerMessage(decrypted_msg,
                               sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid

    email = EmailFactory.fromServerMessage(sender.user_id, decrypted_msg,
                                           wrapped_key, recipient_key_version,
                                           None)
    _verifyEmail(email, pvm, msg)
    assert H.CaseInsensitiveSet(map(lambda u: u["user_id"],
                                    email.bccs)) == H.CaseInsensitiveSet(
                                        map(lambda u: u["user_id"], bccs))

    # bcc is a sub group of one of the tos_groups
    bccs = pvm.tos_groups[random.randint(0, len(pvm.tos_groups) - 1)]["users"]
    msg.wrapped_bccs = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            H.utf8Encode(H.jdumps(bccs))))
    decrypted_msg = decryptServerMessage(
        msg.toDict(), pvm.user_key.encryption_key, pvm.symm_key)
    assert verifyServerMessage(decrypted_msg,
                               sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid
    email = EmailFactory.fromServerMessage(sender.user_id, decrypted_msg,
                                           wrapped_key, recipient_key_version,
                                           None)
    _verifyEmail(email, pvm, msg)
    assert H.CaseInsensitiveSet(map(lambda u: u["user_id"],
                                    email.bccs)) == H.CaseInsensitiveSet(
                                        map(lambda u: u["user_id"], bccs))


def test_server_message_parser_V5():
    sender_key_version = random.randint(0, 100)
    recipient_key_version = random.randint(0, 100)
    sender_user_key = H.PVKeyFactory.newUserKey(key_version=sender_key_version)
    sender = H.UserData(
        randUnicode(6), randUnicode(6), randUnicode(5),
        [sender_user_key.public_user_key], None)
    pvm = MockPrivateMetadataV5(
        sender=sender.user_id, user_key=sender_user_key)
    signature, encrypted_pvm = pvm.signAndEncrypt()

    wrapped_key = b64enc(
        pvm.user_key.public_user_key.public_key.seal(pvm.symm_key.serialize()))

    recipients = [recipient() for _ in range(2)]
    bad_wrapped_recipients = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            H.utf8Encode(H.jdumps(recipients))))

    msg = MockServerMessageV5(encrypted_pvm, signature, sender_key_version,
                              recipient_key_version, wrapped_key,
                              bad_wrapped_recipients)

    u = H.UserData(
        randUnicode(6), randUnicode(6), randUnicode(5),
        [H.PVKeyFactory.newUserKey(key_version=0).public_user_key], None)
    with pytest.raises(H.EmailException):
        # bad wrapped recipients
        decrypted_msg = decryptServerMessage(msg.toDict(), pvm.user_key.encryption_key, pvm.symm_key)

    msg.wrapped_recipients = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            H.utf8Encode(H.jdumps(pvm.tos + pvm.ccs))))
    decrypted_msg = decryptServerMessage(msg.toDict(),
                                         pvm.user_key.encryption_key,
                                         pvm.symm_key)
    assert verifyServerMessage(decrypted_msg,
                               sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid

    email = EmailFactory.fromServerMessage(
        u.user_id, decrypted_msg, wrapped_key, recipient_key_version, None)

    assert email.server_attr.collection_id == sender.mail_cid
    _verifyEmail(email, pvm, msg)
    # bccs can figure out themselves as being bcced
    assert email.bccs == [{"user_id": u.user_id, "display_name": u.user_id}]

    # no bcc
    to = H.UserData(pvm.tos[0]["user_id"], randUnicode(6), randUnicode(5),
                    [H.PVKeyFactory.newUserKey(key_version=0).public_user_key],
                    None)
    email = EmailFactory.fromServerMessage(
        to.user_id, decrypted_msg, wrapped_key, recipient_key_version, None)

    _verifyEmail(email, pvm, msg)
    assert email.bccs == []

    # sender can see all bccs
    bccs = [recipient() for _ in range(3)]
    msg.wrapped_bccs = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            H.utf8Encode(H.jdumps(bccs))))
    decrypted_msg = decryptServerMessage(msg.toDict(),
                                         pvm.user_key.encryption_key,
                                         pvm.symm_key)
    assert verifyServerMessage(decrypted_msg,
                               sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid

    email = EmailFactory.fromServerMessage(sender.user_id, decrypted_msg,
                                           wrapped_key, recipient_key_version,
                                           None)

    _verifyEmail(email, pvm, msg)
    assert H.CaseInsensitiveSet(map(lambda u: u["user_id"],
                                    email.bccs)) == H.CaseInsensitiveSet(
                                        map(lambda u: u["user_id"], bccs))

    # wrong verify key
    bad_user_key = H.PVKeyFactory.newUserKey(key_version=1)
    assert not verifyServerMessage(decrypted_msg,
                                   bad_user_key.public_user_key.verify_key)

    for f in [getSender, getWrappedKey]:
        with pytest.raises(H.EmailException):
            # corrupted message
            decrypted_msg = {}
            f(decrypted_msg)
