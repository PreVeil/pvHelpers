from .email_v2 import EmailV2
from .email_helpers import PROTOCOL_VERSION, EmailHelpers, EmailException
from ..misc import g_log


class EmailV4(EmailV2):
    """Production version: Protocol version 4 is identical to protocol version 2"""
    protocol_version = PROTOCOL_VERSION.V4

    def __init__(self, *args, **kwargs):
        super(EmailV4, self).__init__(*args, **kwargs)

    def indexableAttachmentNames(self):
        return u" ".join(
            map(
                lambda att: att.metadata.filename,
                filter(
                    lambda att: att.metadata.filename is not None or att.metadata.
                    filename != u"untitled", self.attachments)))

    def indexableRecipients(self):
        all_recips = [
            recip["display_name"] + u" " + recip["user_id"]
            for recip in [self.sender] + self.tos + self.ccs + self.bccs
        ]
        return u" ".join(all_recips)

    def indexableBody(self):
        # TODO: striphtml and search in html!
        try:
            body = EmailHelpers.deserializeBody(self.body.content)
        except EmailException as e:
            g_log.exception(e)
            return u""

        return body["text"]
