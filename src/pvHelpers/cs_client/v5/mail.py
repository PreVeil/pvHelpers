from pvHelpers.user import LocalUser, UserDBNode
from pvHelpers.utils import params


class MailV5(object):
    @params(object, LocalUser, unicode, int, int)
    def getPaginatedThreads(self, user, mailbox_id, limit, offset):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/mail/{}/mailboxes/{}/threads".format(user.mail_cid, mailbox_id),
            "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
            "limit" : limit,
            "offset": offset
        })
        resp.raise_for_status()
        return resp.json()


    @params(object, {LocalUser, UserDBNode}, {int, long}, unicode, unicode, unicode)
    def getMailHistoryForExport(self, user, last_rev_id, for_user_id, for_user_cid, export_id):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/mail/{}/mailboxes".format(for_user_id),
            "GET", None, False, (export_id, for_user_id)
        )
        resp = self.get(url, headers, raw_body, params={
            "since_rev_id" : last_rev_id,
        })
        resp.raise_for_status()
        return resp.json()
