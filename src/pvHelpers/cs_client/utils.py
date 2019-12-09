import types

from pvHelpers.utils import params
from requests import codes


class ServerResponseError(Exception):
    def __init__(self, exception=u""):
        super(ServerResponseError, self).__init__(exception)


class ExpiredDeviceKey(Exception):
    def __init__(self, user_id, account_version, key_version, exception=u""):
        super(ExpiredDeviceKey, self).__init__(exception)
        self.user_id = user_id
        self.account_version = account_version
        self.key_version = key_version

        self.exception = exception


class ExpiredUserKey(Exception):
    def __init__(self, exception=u"", key_version=None):
        super(ExpiredUserKey, self).__init__(exception)
        self.expected_user_key_version = key_version


class UnauthorizedReqLimitException(Exception):
    def __init__(self, exception=u""):
        super(UnauthorizedReqLimitException, self).__init__(exception)


class RequestError(Exception):
    class InternalCodes(object):
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
    def BadParameter(cls, errors):  # noqa: N802
        return cls(codes.bad_request, u"invalid-params", errors)

    @classmethod
    def ProxyAuth(cls, errors):  # noqa: N802
        # codes.proxy_authentication_required is not supported by FE
        # use 511 Network Authentication Required for now
        return cls(511, u"proxy-auth-required", errors)

    @classmethod
    def ProxyError(cls, errors):  # noqa: N802
        # need a better status_code
        return cls(512, u"proxy-error", errors)

    @classmethod
    def Forbidden(cls, errors):  # noqa: N802
        return cls(codes.forbidden, u"forbidden", errors)

    @classmethod
    def Expired(cls, errors):  # noqa: N802
        return cls(cls.InternalCodes.EXPIRED, u"expired", errors)

    @classmethod
    def NotFound(cls, errors):  # noqa: N802
        return cls(codes.not_found, u"missing-entity", errors)

    @classmethod
    def Conflict(cls, errors):  # noqa: N802
        return cls(codes.conflict, u"conflict", errors)
