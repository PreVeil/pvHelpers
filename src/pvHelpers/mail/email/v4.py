from pvHelpers.logger import g_log

from .helpers import EmailException, EmailHelpers, PROTOCOL_VERSION
from .v2 import EmailV2


class EmailV4(EmailV2):
    """Production version: Protocol version 4 is identical to protocol version 2"""
    protocol_version = PROTOCOL_VERSION.V4

    def __init__(self, *args, **kwargs):
        super(EmailV4, self).__init__(*args, **kwargs)

    def indexable_attachment_names(self):
        return u" ".join(
            map(
                lambda att: att.metadata.filename,
                filter(
                    lambda att: att.metadata.filename is not None or att.metadata.filename != u"untitled",
                    self.attachments)))

    def indexable_recipients(self):
        all_recips = [
            recip["display_name"] + u" " + recip["user_id"]
            for recip in [self.sender] + self.tos + self.ccs + self.bccs
        ]
        return u" ".join(all_recips)

    def indexable_body(self):
        # TODO: striphtml and search in html!
        try:
            body = EmailHelpers.deserialize_body(self.body.content)
        except EmailException as e:
            g_log.exception(e)
            return u""

        return body["text"]
