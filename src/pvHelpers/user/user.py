from pvHelpers.utils import params


class User(object):
    def __init__(self, user_id, account_version, display_name, mail_cid, public_user_keys, organiztion_info):
        self.user_id = user_id
        self.account_version = account_version
        self.display_name = display_name
        self.mail_cid = mail_cid
        self.public_user_keys = public_user_keys
        self.org_info = organiztion_info

    @property
    def public_user_key(self):
        if not self.public_user_keys:
            raise ValueError("No Public user keys available!")

        return sorted(self.public_user_keys, key=lambda k: k.key_version, reverse=True)[0]

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "account_version": self.account_version,
            "display_name": self.display_name,
            "mail_cid": self.mail_cid,
            "org_info": self.org_info if self.org_info is None else self.org_info.to_dict()
        }

    def is_claimed(self):
        return len(self.public_user_keys) > 0

    @params(object, {int, long})
    def get_public_user_key_with_version(self, version=-1):
        if version == -1:
            return self.public_user_key
        return next(k for k in self.public_user_keys if k.key_version == version)


class OrganizationInfo(object):
    def __init__(self, organiztion_id, organiztion_name, department_name, role):
        self.org_id = organiztion_id
        self.org_name = organiztion_name
        self.dept_name = department_name
        self.role = role

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.to_dict() == other.to_dict()
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def to_dict(self):
        return {
            "org_id": self.org_id,
            "org_name": self.org_name,
            "dept_name": self.dept_name,
            "role": self.role
        }
