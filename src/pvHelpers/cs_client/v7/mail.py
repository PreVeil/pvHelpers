from pvHelpers.mail.prepared_message import PreparedMessageBase
from pvHelpers.user import LocalUser
from pvHelpers.utils import params


class MailV7(object):
    @params(object, LocalUser, PreparedMessageBase)
    def send_email(self, user, prepared_message):
        # this uploads to sender's mail_cid
        self.uploadEmailBlocks(user, prepared_message)
        url, raw_body, headers = self.prepareSignedRequest(
            user, "/mail/send",
            "POST", prepared_message.to_dict()
        )
        resp = self.post(url, headers, raw_body)
        resp.raise_for_status()
        return resp.json()
