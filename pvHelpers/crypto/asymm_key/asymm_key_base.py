class AsymmKeyBase(object):
    def __init__(self, protocol_version):
        self.protocol_version = protocol_version

    @property
    def public_key(self):
        raise NotImplementedError("children must have public_key property")

    def unseal(self, message):
        raise NotImplementedError("unseal must be implemented by children")

    def serialize(self):
        raise NotImplementedError("serialize must be implemented by children")


class PublicKeyBase(object):
    def __init__(self, protocol_version):
        self.protocol_version = protocol_version

    def seal(self, message):
        raise NotImplementedError("seal must be implemented by children")

    def serialize(self):
        raise NotImplementedError("serialize must be implemented by children")
