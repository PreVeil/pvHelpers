from pvHelpers.user import LocalUser
from pvHelpers.utils import params


class MailV5(object):
    @params(object, LocalUser, unicode, int, int)
    def get_paginated_threads(self, user, mailbox_id, limit, offset):
        url, raw_body, headers = self.prepareSignedRequest(
            user,  u"/mail/{}/mailboxes/{}/threads".format(user.mail_cid, mailbox_id),
            "GET", None
        )
        resp = self.get(url, headers, raw_body, params={
            "limit": limit,
            "offset": offset
        })
        resp.raise_for_status()
        return resp.json()
