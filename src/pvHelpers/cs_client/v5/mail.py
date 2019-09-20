import pvHelpers as H


class MailV5(object):
    @H.params(object, H.LocalUser, unicode, int, int)
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
