from pvHelpers.utils import params


class UserGroup(object):
    @params(object, unicode, [unicode])
    def __init__(self, address, members):
        self.address = address
        self.members = members

    def to_dict(self):
        return {
            "alias": self.address,
            "users": self.members
        }
