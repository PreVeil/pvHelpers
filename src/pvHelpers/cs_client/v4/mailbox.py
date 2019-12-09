from pvHelpers.user import LocalUser
from pvHelpers.utils import params, to_int

from ..utils import ServerResponseError


class MailboxV4(object):
    @params(object, LocalUser, unicode)
    def create_mailbox(self, user, name):
        url, raw_body, headers = self.prepare_signed_request(
            user, "/mail/{}/mailboxes".format(user.mail_cid),
            "POST", {"name": name}
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        try:
            data = resp.json()
            return data["mailbox_id"], data["rev_id"]
        except (KeyError, ValueError) as e:
            raise ServerResponseError(e)

    @params(object, LocalUser, unicode, unicode)
    def rename_mailbox(self, user, server_id, new_name):
        url, raw_body, headers = self.prepare_signed_request(
            user, "/mail/{}/mailboxes/{}".format(user.mail_cid, server_id),
            "PUT", {"name": new_name}
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        try:
            data = resp.json()
            return data["rev_id"]
        except (KeyError, ValueError) as e:
            raise ServerResponseError(e)

    @params(object, LocalUser, unicode)
    def delete_mailbox(self, user, server_id):
        url, raw_body, headers = self.prepare_signed_request(
            user, "/mail/{}/mailboxes/{}".format(user.mail_cid, server_id),
            "DELETE", None
        )
        resp = self.delete(url, headers, params={})
        resp.raise_for_status()
        try:
            data = resp.json()
            return data["rev_id"]
        except (KeyError, ValueError) as e:
            raise ServerResponseError(e)

    @params(object, LocalUser, unicode)
    def get_mailbox_next_uid(self, user, mailbox_id):
        url, raw_body, headers = self.prepare_signed_request(
            user,  u"/mail/{}/mailboxes/{}/uid".format(user.mail_cid, mailbox_id),
            "GET", None
        )
        resp = self.get(url, headers, raw_body)
        resp.raise_for_status()
        data = resp.json()
        next_uid = data.get("next_uid")
        if not next_uid:
            raise ServerResponseError("'next_uid' missing")
        status, next_uid = to_int(next_uid)
        if not status:
            raise ServerResponseError("int coercion failed")
        return next_uid

    @params(object, LocalUser, int)
    def get_user_mailboxes(self, user, since_rev_id=0):
        url, raw_body, headers = self.prepare_signed_request(
            user,  u"/mail/{}/mailboxes".format(user.mail_cid),
            "GET", None
        )
        resp = self.get(url, headers, params={"since_rev_id": since_rev_id, "fetch_messages": u"false"})
        resp.raise_for_status()
        return resp.json()
