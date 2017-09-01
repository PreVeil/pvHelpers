from . import EmailHelpers, EmailBase

class EmailV3(EmailHelpers, EmailBase):
    def __init__(self):
        super(EmailV3, self).__init__()
