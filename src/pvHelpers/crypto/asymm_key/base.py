class AsymmKeyBase(object):
    def __init__(self, protocol_version):
        self.protocol_version = protocol_version

    @property
    def public_key(self):
        raise NotImplementedError("children must have public_key property")

    @property
    def key(self):
        raise NotImplementedError("children must have `key` property")

    @property
    def buffer(self):
        raise NotImplementedError("buffer must be implemented by children")

    def serialize(self):
        raise NotImplementedError("serialize must be implemented by children")

    def __eq__(self, *args, **kwargs):
        raise NotImplementedError("children must implement __eq__")

    def __ne__(self, *args, **kwargs):
        raise NotImplementedError("children must implement __ne__")


class PublicKeyBase(object):
    def __init__(self, protocol_version):
        self.protocol_version = protocol_version

    @property
    def key(self):
        raise NotImplementedError("children must have `key` property")

    @property
    def buffer(self):
        raise NotImplementedError("buffer must be implemented by children")

    def serialize(self):
        raise NotImplementedError("serialize must be implemented by children")
