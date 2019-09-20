import calendar
import time

import pvHelpers as H


class MailV4(object):
    @H.params(object, H.LocalUser, H.PreparedMessageBase)
    def sendEmail(self, user, prepared_message):
        self.uploadEmailBlocks(user, prepared_message)
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/mail/{}".format(prepared_message.recipient.mail_cid),
            "POST", prepared_message.toDict()
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()

    @H.params(object, H.LocalUser, H.PreparedMessageBase, unicode)
    def appendEmailToMailbox(self, user, prepared_message, mailbox_id):
        self.uploadEmailBlocks(user, prepared_message)
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/mail/{}/mailboxes/{}/messages".format(user.mail_cid, mailbox_id),
            "POST", {"message" : prepared_message.toDict()}
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        try:
            data = resp.json()
            # converting timestamp to unix epoch int
            data["timestamp"] = calendar.timegm(time.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S"))
        except (KeyError, ValueError) as e:
            raise H.ServerResponseError(e)
        return data

    @H.params(object, {H.LocalUser, H.UserDBNode}, unicode, [{"id": unicode, "last_version": unicode, "flags": [unicode]}])
    def updateFlags(self, user, mailbox_id, updates):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/mail/{}/mailboxes/{}/messages".format(user.mail_cid, mailbox_id),
            "PATCH", {u"updates": updates}
        )
        resp = self.patch(url, headers, raw_body)
        resp.raise_for_status()
        try:
            data = resp.json()
            return data["data"]
        except (KeyError. ValueError) as e:
            raise H.ServerResponseError(e)

    @H.params(object, {H.LocalUser, H.UserDBNode}, unicode, unicode, [{int, long}])
    def dupeMessages(self, user, src_mailbox_id, dest_mailbox_id, uids):
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/mail/{}/mailboxes/{}/messages/copy".format(user.mail_cid, dest_mailbox_id),
            "POST", {u"source_mbid" : src_mailbox_id, u"uids" : uids}
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        try:
            data = resp.json()
            data = data["data"]
            for update in data:
                timestamp = update["result"]["timestamp"]
                update["result"]["timestamp"] = calendar.timegm(time.strptime(timestamp, "%Y-%m-%dT%H:%M:%S"))
        except (KeyError, ValueError) as e:
            raise H.ServerResponseError(e)

        return data

    @H.params(object, {H.LocalUser, H.UserDBNode}, {int, long})
    def getMailHistory(self, user, last_rev_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/mail/{}/mailboxes".format(user.mail_cid),
            "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
            "since_rev_id" : last_rev_id,
        })
        resp.raise_for_status()
        return resp.json()

    @H.params(object, {H.LocalUser, H.UserDBNode}, unicode, unicode)
    def expungeEmail(self, user, mailbox_id, email_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user, u"/mail/{}/mailboxes/{}/messages/{}".format(user.mail_cid, mailbox_id, email_id),
            "DELETE", None
        )
        resp = self.delete(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()

    @H.params(object, {H.LocalUser, H.UserDBNode}, unicode)
    def getMailboxUnseenCount(self, user, mailbox_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/mail/{}/mailboxes/{}/unseen_count".format(user.mail_cid, mailbox_id),
            "GET", None
        )
        resp = self.get(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
