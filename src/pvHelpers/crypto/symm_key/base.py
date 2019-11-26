from pvHelpers.utils import params


class SymmKeyBase(object):
    @params(object, int)
    def __init__(self, protocol_version):
        self.protocol_version = protocol_version

    @property
    def secret(self):
        raise NotImplementedError("secret must be implemented by children")

    def serialize(self):
        raise NotImplementedError("serialize must be implemented by children")

    def __eq__(self, other):
        raise NotImplementedError("__eq__ must be implemented by children")

    def __ne__(self, other):
        raise NotImplementedError("__ne__ must be implemented by children")
