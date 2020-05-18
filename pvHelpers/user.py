import requests, types
from .crypto import PVKeyFactory
from . import misc
from .luser_info import LUserInfo
from .params import params


class OrganizationInfo(object):
    def __init__(self, organization_id, organization_name, department_name, role, show_mua_prompt):
        self.org_id = organization_id
        self.org_name = organization_name
        self.dept_name = department_name
        self.role = role
        self.show_mua_prompt = show_mua_prompt

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.toDict() == other.toDict()
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def toDict(self):
        return {
            "org_id": self.org_id,
            "org_name": self.org_name,
            "dept_name": self.dept_name,
            "role": self.role,
            "show_mua_prompt": self.show_mua_prompt
        }


# Model for User Bucket protocol_version=1
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


class UserData(object):
    def __init__(self, user_id, display_name, mail_cid, public_user_keys, organization_info):
        self.user_id = user_id
        self.display_name = display_name
        self.mail_cid = mail_cid
        self.public_user_keys = public_user_keys
        self.org_info = organization_info

    @property
    def public_user_key(self):
        if not self.public_user_keys:
            raise ValueError("No Public user keys available!")

        return sorted(self.public_user_keys, key=lambda k: k.key_version, reverse=True)[0]

    def toDict(self):
        return {
            "user_id" : self.user_id,
            "display_name" : self.display_name,
            "mail_cid" : self.mail_cid,
            "org_info" : self.org_info if self.org_info is None else self.org_info.toDict()
        }
    def isClaimed(self):
        return len(self.public_user_keys) > 0

    @params(object, {int, long})
    def getPublicUserKeyWithVersion(self, version=-1):
        if version == -1:
            return self.public_user_key
        return next(k for k in self.public_user_keys if k.key_version == version)
