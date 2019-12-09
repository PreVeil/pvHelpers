# vim: set fileencoding=utf-8 :
import random

from mocks import (MockPrivateMetadataV5, MockPrivateMetadataV6,
                   MockServerMessageV5, MockServerMessageV6, recipient)
from pvHelpers.crypto import PVKeyFactory
from pvHelpers.mail import (decrypt_server_message, EmailFactory,
                            flatten_recipient_groups, get_sender,
                            get_wrapped_key, verify_server_message)
from pvHelpers.mail.email import EmailException, PROTOCOL_VERSION
from pvHelpers.user import User
from pvHelpers.utils import (b64enc, CaseInsensitiveSet, jdumps, rand_unicode,
                             utf8_encode)
import pytest


def _verify_recipients(email, pvm):
    if pvm.protocol_version == PROTOCOL_VERSION.V5:
        assert CaseInsensitiveSet(
            map(lambda u: u["user_id"], email.tos)) == CaseInsensitiveSet(
                map(lambda u: u["user_id"], pvm.tos))
        assert CaseInsensitiveSet(
            map(lambda u: u["user_id"], email.ccs)) == CaseInsensitiveSet(
                map(lambda u: u["user_id"], pvm.ccs))
    elif pvm.protocol_version == PROTOCOL_VERSION.V6:
        assert CaseInsensitiveSet(
            map(lambda u: u["user_id"], email.tos)) == CaseInsensitiveSet(
                map(lambda u: u["user_id"], pvm.tos) +
                map(lambda u: u["alias"], pvm.tos_groups))

        # check group mapping is correct in the Email obj
        t = {}
        for tg in pvm.tos_groups:
            t[tg["alias"]] = tg["users"]

        for to in email.tos:
            if to.get("members", None):
                assert to["members"] == t[to["user_id"]]

        assert CaseInsensitiveSet(
            map(lambda u: u["user_id"], email.ccs)) == CaseInsensitiveSet(
                map(lambda u: u["user_id"], pvm.ccs) +
                map(lambda u: u["alias"], pvm.ccs_groups))

        t = {}
        for tg in pvm.ccs_groups:
            t[tg["alias"]] = tg["users"]

        for cc in email.ccs:
            if cc.get("members", None):
                assert cc["members"] == t[cc["user_id"]]

    else:
        raise ValueError("unsupported protocol version {}".format(pvm.protocol_version))


def _verify_email(email, pvm, msg):
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


def test_server_message_parser_v6():
    sender_key_version = random.randint(0, 100)
    recipient_key_version = random.randint(0, 100)
    sender_user_key = PVKeyFactory.new_user_key(key_version=sender_key_version)
    sender = User(
        rand_unicode(6), random.randint(0, 99999), rand_unicode(6),
        rand_unicode(5), [sender_user_key.public_user_key], None)
    pvm = MockPrivateMetadataV6(sender=sender.user_id, user_key=sender_user_key)
    signature, encrypted_pvm = pvm.sign_and_encrypt()

    wrapped_key = b64enc(
        pvm.user_key.public_user_key.public_key.seal(pvm.symm_key.serialize()))

    tos_groups_flatten = flatten_recipient_groups(pvm.tos_groups)
    ccs_groups_flatten = flatten_recipient_groups(pvm.ccs_groups)
    wrapped_recipients = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            utf8_encode(jdumps(pvm.tos + pvm.ccs + tos_groups_flatten + ccs_groups_flatten))))

    msg = MockServerMessageV6(encrypted_pvm, signature, sender_key_version,
                              recipient_key_version, wrapped_key,
                              wrapped_recipients)

    decrypted_msg = decrypt_server_message(
        msg.to_dict(), pvm.user_key.encryption_key, pvm.symm_key)
    assert verify_server_message(
        decrypted_msg, sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid

    email = EmailFactory.from_server_message(sender.user_id, decrypted_msg, wrapped_key, recipient_key_version, None)
    assert email.server_attr.collection_id == sender.mail_cid
    _verify_email(email, pvm, msg)

    # sender can see all bccs
    bccs = [recipient() for _ in range(3)]
    msg.wrapped_bccs = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            utf8_encode(jdumps(bccs))))
    decrypted_msg = decrypt_server_message(
        msg.to_dict(), pvm.user_key.encryption_key, pvm.symm_key)
    assert verify_server_message(
        decrypted_msg, sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid

    email = EmailFactory.from_server_message(
        sender.user_id, decrypted_msg, wrapped_key, recipient_key_version, None)
    _verify_email(email, pvm, msg)
    assert CaseInsensitiveSet(map(lambda u: u["user_id"], email.bccs)) == \
        CaseInsensitiveSet(map(lambda u: u["user_id"], bccs))

    # bcc is a sub group of one of the tos_groups
    bccs = pvm.tos_groups[random.randint(0, len(pvm.tos_groups) - 1)]["users"]
    msg.wrapped_bccs = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            utf8_encode(jdumps(bccs))))
    decrypted_msg = decrypt_server_message(
        msg.to_dict(), pvm.user_key.encryption_key, pvm.symm_key)
    assert verify_server_message(
        decrypted_msg, sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid
    email = EmailFactory.from_server_message(
        sender.user_id, decrypted_msg, wrapped_key, recipient_key_version, None)
    _verify_email(email, pvm, msg)
    assert CaseInsensitiveSet(map(lambda u: u["user_id"], email.bccs)) == \
        CaseInsensitiveSet(map(lambda u: u["user_id"], bccs))


def test_server_message_parser_v5():
    sender_key_version = random.randint(0, 100)
    recipient_key_version = random.randint(0, 100)
    sender_user_key = PVKeyFactory.new_user_key(key_version=sender_key_version)
    sender = User(
        rand_unicode(6), random.randint(0, 99999), rand_unicode(6),
        rand_unicode(5), [sender_user_key.public_user_key], None)
    pvm = MockPrivateMetadataV5(
        sender=sender.user_id, user_key=sender_user_key)
    signature, encrypted_pvm = pvm.sign_and_encrypt()

    wrapped_key = b64enc(
        pvm.user_key.public_user_key.public_key.seal(pvm.symm_key.serialize()))

    recipients = [recipient() for _ in range(2)]
    bad_wrapped_recipients = b64enc(
        pvm.user_key.public_user_key.public_key.seal(utf8_encode(jdumps(recipients))))

    msg = MockServerMessageV5(
        encrypted_pvm, signature, sender_key_version,
        recipient_key_version, wrapped_key, bad_wrapped_recipients)

    u = User(
        rand_unicode(6), random.randint(0, 99999), rand_unicode(6), rand_unicode(5),
        [PVKeyFactory.new_user_key(key_version=0).public_user_key], None)
    with pytest.raises(EmailException):
        # bad wrapped recipients
        decrypted_msg = decrypt_server_message(msg.to_dict(), pvm.user_key.encryption_key, pvm.symm_key)

    msg.wrapped_recipients = b64enc(
        pvm.user_key.public_user_key.public_key.seal(
            utf8_encode(jdumps(pvm.tos + pvm.ccs))))
    decrypted_msg = decrypt_server_message(
        msg.to_dict(), pvm.user_key.encryption_key, pvm.symm_key)
    assert verify_server_message(
        decrypted_msg, sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid

    email = EmailFactory.from_server_message(
        u.user_id, decrypted_msg, wrapped_key, recipient_key_version, None)

    assert email.server_attr.collection_id == sender.mail_cid
    _verify_email(email, pvm, msg)
    # bccs can figure out themselves as being bcced
    assert email.bccs == [{"user_id": u.user_id, "display_name": u.user_id}]

    # no bcc
    to = User(
        pvm.tos[0]["user_id"], random.randint(0, 99999), rand_unicode(6), rand_unicode(5),
        [PVKeyFactory.new_user_key(key_version=0).public_user_key], None)
    email = EmailFactory.from_server_message(
        to.user_id, decrypted_msg, wrapped_key, recipient_key_version, None)

    _verify_email(email, pvm, msg)
    assert email.bccs == []

    # sender can see all bccs
    bccs = [recipient() for _ in range(3)]
    msg.wrapped_bccs = b64enc(
        pvm.user_key.public_user_key.public_key.seal(utf8_encode(jdumps(bccs))))
    decrypted_msg = decrypt_server_message(
        msg.to_dict(), pvm.user_key.encryption_key, pvm.symm_key)
    assert verify_server_message(
        decrypted_msg, sender.public_user_key.verify_key)
    decrypted_msg["collection_id"] = sender.mail_cid

    email = EmailFactory.from_server_message(
        sender.user_id, decrypted_msg, wrapped_key, recipient_key_version, None)

    _verify_email(email, pvm, msg)
    assert CaseInsensitiveSet(map(lambda u: u["user_id"], email.bccs)) == \
        CaseInsensitiveSet(map(lambda u: u["user_id"], bccs))

    # wrong verify key
    bad_user_key = PVKeyFactory.new_user_key(key_version=1)
    assert not verify_server_message(
        decrypted_msg, bad_user_key.public_user_key.verify_key)

    for f in [get_sender, get_wrapped_key]:
        with pytest.raises(EmailException):
            # corrupted message
            decrypted_msg = {}
            f(decrypted_msg)
