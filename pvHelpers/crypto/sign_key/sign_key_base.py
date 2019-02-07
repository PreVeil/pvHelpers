class SignKeyBase(object):

    def __init__(self, protocol_version):
        self.protocol_version = protocol_version

    @property
    def key(self):
        raise NotImplementedError("children must have `key` property")

    @property
    def verify_key(self):
        raise NotImplementedError("children must have verifier property")

    @property
    def buffer(self):
        raise NotImplementedError("children must have buffer property")

    def signText(self, *args, **kwargs):
        raise NotImplementedError("signText must be implemented by children")

    def signBinary(self, *args, **kwargs):
        raise NotImplementedError("signBinary must be implemented by children")

    def serialize(self):
        raise NotImplementedError("serialize must be implemented by children")

    def __eq__(self, *args, **kwargs):
        raise NotImplementedError("children must implement __eq__")

    def __ne__(self, *args, **kwargs):
        raise NotImplementedError("children must implement __ne__")

class VerifyKeyBase(object):
    def __init__(self, protocol_version):
        self.protocol_version = protocol_version

    @property
    def key(self):
        raise NotImplementedError("children must have `key` property")

    @property
    def buffer(self):
        raise NotImplementedError("children must have buffer property")

    def verifyText(self, *args, **kwargs):
        raise NotImplementedError("verifyText must be implemented by children")

    def verifyBinary(self, *args, **kwargs):
        raise NotImplementedError("verifyBinary must be implemented by children")

    def serialize(self):
        raise NotImplementedError("serialize must be implemented by children")
