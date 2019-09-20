# legacy model for User Bucket protocol_version=1
class UserDBNode(object):
    @staticmethod
    def new(user_id, display_name, mail_cid, password, org_info, luser_info):
        if not isinstance(user_id, unicode):
            return False, None
        if not isinstance(display_name, unicode):
            return False, None
        if not isinstance(mail_cid, unicode):
            return False, None
        if not isinstance(password, unicode):
            return False, None
        if not isinstance(org_info, (types.NoneType, OrganizationInfo)):
            return False, None
        if not isinstance(luser_info, (LUserInfo, misc.NOT_ASSIGNED)):
            return False, None

        return True, UserDBNode(user_id, display_name, mail_cid, password, org_info, luser_info)

    def __init__(self, user_id, display_name, mail_cid, password, org_info, luser_info):
        self.user_id = user_id
        self.display_name = display_name
        self.mail_cid = mail_cid
        self.password = password
        self.org_info = org_info
        self.luser_info = luser_info

    def toDict(self):
        return {
            "user_id" : self.user_id,
            "display_name" : self.display_name,
            "mail_cid" : self.mail_cid,
            "password" : self.password,
            "org_info" : self.org_info if self.org_info is None else self.org_info.toDict(),
            "luser_info" : str(self.luser_info)
        }
