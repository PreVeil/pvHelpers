import calendar
import time

import pvHelpers as H


class MailboxV4(object):
    @H.params(object, {H.UserDBNode, H.LocalUser}, unicode)
    def createMailbox(self, user, name):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/mail/{}/mailboxes".format(user.mail_cid),
            "POST", {"name" : name}
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        try:
            data = resp.json()
            return data["mailbox_id"], data["rev_id"]
        except (KeyError, ValueError) as e:
            raise H.ServerResponseError(e)

    @H.params(object, {H.UserDBNode, H.LocalUser}, unicode, unicode)
    def renameMailbox(self, user, server_id, new_name):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/mail/{}/mailboxes/{}".format(user.mail_cid, server_id),
            "PUT", {"name" : new_name}
        )
        resp = self.put(url, headers, raw_body)
        resp.raise_for_status()
        try:
            data = resp.json()
            return data["rev_id"]
        except (KeyError, ValueError) as e:
            raise H.ServerResponseError(e)

    @H.params(object, {H.UserDBNode, H.LocalUser}, unicode)
    def deleteMailbox(self, user, server_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/mail/{}/mailboxes/{}".format(user.mail_cid, server_id),
            "DELETE", None
        )
        resp = self.delete(url, headers, params={})
        resp.raise_for_status()
        try:
            data = resp.json()
            return data["rev_id"]
        except (KeyError, ValueError) as e:
            raise H.ServerResponseError(e)

    @H.params(object, {H.UserDBNode, H.LocalUser}, unicode)
    def getMailboxNextUID(self, user, mailbox_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/mail/{}/mailboxes/{}/uid".format(user.mail_cid, mailbox_id),
            "GET", None
        )
        resp = self.get(url, headers, raw_body)
        resp.raise_for_status()
        data = resp.json()
        next_uid = data.get("next_uid")
        if not next_uid:
            raise H.ServerResponseError("'next_uid' missing")
        status, next_uid = H.toInt(next_uid)
        if not status:
            raise H.ServerResponseError("int coercion failed")
        return next_uid

    @H.params(object, {H.UserDBNode, H.LocalUser}, int)
    def getUserMailboxes(self, user, since_rev_id=0):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/mail/{}/mailboxes".format(user.mail_cid),
            "GET", None
        )
        resp = self.get(url, headers, params={"since_rev_id": since_rev_id, "fetch_messages": u"false"})
        resp.raise_for_status()
        return resp.json()
