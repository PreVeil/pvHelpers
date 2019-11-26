class UserKeyBase(object):
    def __init__(self, protocol_version, key_version):
        self.protocol_version = protocol_version
        self.key_version = key_version

    @property
    def encryption_key(self):
        raise NotImplementedError("children must have encryption_key property")

    @property
    def signing_key(self):
        raise NotImplementedError("children must have signing_key property")

    @property
    def public_user_key(self):
        raise NotImplementedError("children must have public_user_key property")

    def __eq__(self, *args, **kwargs):
        raise NotImplementedError("children must implement __eq__")

    def __ne__(self, *args, **kwargs):
        raise NotImplementedError("children must implement __ne__")

    def serialize(self):
        raise NotImplementedError("children must implement serialize")

    @classmethod
    def deserialize(cls, *args, **kwargs):
        raise NotImplementedError("children must implement deserialize")


class PublicUserKeyBase(object):
    def __init__(self, protocol_version, key_version):
        self.protocol_version = protocol_version
        self.key_version = key_version

    @property
    def public_key(self):
        raise NotImplementedError("children must have public_key property")

    @property
    def verify_key(self):
        raise NotImplementedError("children must have verify_key property")

    def serialize(self):
        raise NotImplementedError("children must implement serialize")

    @classmethod
    def deserialize(cls, *args, **kwargs):
        raise NotImplementedError("children must implement deserialize")
