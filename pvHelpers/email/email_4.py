from .email_base import EmailBase
from .email_helpers import EmailHelpers

class EmailV4(EmailHelpers, EmailBase):
    def __init__(self):
        super(EmailV4, self).__init__()
