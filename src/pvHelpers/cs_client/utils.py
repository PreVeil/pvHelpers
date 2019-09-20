import types

from pvHelpers.utils import params


class ServerResponseError(Exception):
    def __init__(self, exception=u""):
        super(ServerResponseError, self).__init__(exception)


class ExpiredDeviceKey(Exception):
    def __init__(self, exception=u""):
        super(ExpiredDeviceKey, self).__init__(exception)


class ExpiredUserKey(Exception):
    def __init__(self, exception=u"", key_version=None):
        super(ExpiredUserKey, self).__init__(exception)
        self.expected_user_key_version = key_version

class UnauthorizedReqLimitException(Exception):
    def __init__(self, exception=u""):
        super(UnauthorizedReqLimitException, self).__init__(exception)


class RequestError(Exception):
    class codes(object):
        EXPIRED = 499

    # cause must be any object that is serializable as string (implements `__str__`)
    # TODO: params can accept interface types to handle ^
    @params(object, int, unicode, [{"source": {types.NoneType, unicode}, "cause": {types.NoneType, unicode}}])
    def __init__(self, status_code, title, errors):
        super(RequestError, self).__init__(
            u"client request error ({}, {}, {})".format(status_code, title, errors))
        self.status_code = status_code
        self.title = title
        self.errors = errors

    @classmethod
    def BadParameter(cls, errors):
        return cls(codes.bad_request, u"invalid-params", errors)

    @classmethod
    def ProxyAuth(cls, errors):
        # codes.proxy_authentication_required is not supported by FE
        # use 511 Network Authentication Required for now
        return cls(511, u"proxy-auth-required", errors)

    @classmethod
    def ProxyError(cls, errors):
        # need a better status_code
        return cls(512, u"proxy-error", errors)

    @classmethod
    def Forbidden(cls, errors):
        return cls(codes.forbidden, u"forbidden", errors)

    @classmethod
    def Expired(cls, errors):
        return cls(cls.codes.EXPIRED, u"expired", errors)

    @classmethod
    def NotFound(cls, errors):
        return cls(codes.not_found, u"missing-entity", errors)

    @classmethod
    def Conflict(cls, errors):
        return cls(codes.conflict, u"conflict", errors)
