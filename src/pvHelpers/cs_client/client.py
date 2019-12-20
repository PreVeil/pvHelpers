import datetime
import inspect

from pvHelpers.http_client import SessionPool
from pvHelpers.logger import g_log
from pvHelpers.user import LocalUser
import requests

from .utils import (ExpiredDeviceKey, ExpiredUserKey, RequestError,
                    UnauthorizedReqLimitException)
from .v4 import APIClientV4
from .v5 import APIClientV5
from .v6 import APIClientV6
from .v7 import APIClientV7


class CSClient(object):
    __api_versions__ = [
        (APIClientV5.__api_version__, APIClientV5),
        (APIClientV4.__api_version__, APIClientV4),
        (APIClientV6.__api_version__, APIClientV6),
        (APIClientV7.__api_version__, APIClientV7)
    ]
    __current_version__ = 7

    _MAX_UNAUTHORIZED_COUNT = 25

    # only call this from _handlers_wrapper
    def _is_user_synced(self, user_id):
        return (user_id not in self.users_sync or
                self.users_sync[user_id]["401_exception_count"] <= self._MAX_UNAUTHORIZED_COUNT)

    # TODO: use this method to reset 401 count after CryptoStore has updated the user; eg in the case of rekey
    def reset_user_unauthorized_state(self, user_id):
        if user_id not in self.users_sync:
            g_log.warn(
                "{} does not encounter any unauthorized request yet.".format(user_id))
            return
        self.users_sync.pop(user_id)

    def _handlers_wrapper(self, fun):  # noqa: C901
        def __wrapper(*args, **kwargs):
            if args and isinstance(args[0], LocalUser):
                u = args[0]
                if not self._is_user_synced(u.user_id):
                    # user has too many 401 unauthorized response
                    time_diff = datetime.datetime.now(
                    ) - self.users_sync[u.user_id]["latest_req_time"]
                    if time_diff.days >= 1:
                        # reset 401 exceptions allowances after one day
                        self.users_sync.pop(u.user_id)
                    else:
                        raise UnauthorizedReqLimitException(
                            u"User {} reached max limit of 401 unauthorized req!".format(u.user_id))

                try:
                    return fun(*args, **kwargs)
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 440:
                        raise ExpiredDeviceKey(u.user_id, u.account_version, u.device.key.key_version, e)
                    elif e.response.status_code == 498:
                        error_ = e.response.json()
                        # can server do something malicious by returning bad expected key_version ?
                        raise ExpiredUserKey(
                            e, error_["errors"][0]["cause"]["expected_version"])
                    elif e.response.status_code == 401:
                        if u.user_id not in self.users_sync:
                            self.users_sync[u.user_id] = {
                                "401_exception_count": 1, "latest_req_time": datetime.datetime.now()}
                        else:
                            self.users_sync[u.user_id]["401_exception_count"] += 1
                            self.users_sync[u.user_id]["latest_req_time"] = datetime.datetime.now(
                            )

                    elif e.response.status_code == 407:
                        g_log.exception(e)
                        raise RequestError.ProxyAuth(
                            [{"cause": u"proxy config required auth", "source": unicode(fun.__name__)}])

                    raise

                except requests.exceptions.ProxyError as e:
                    if str(407) in str(e):
                        raise RequestError.ProxyAuth(
                            [{"cause": u"proxy config required auth", "source": unicode(fun.__name__)}])

                    raise

            return fun(*args, **kwargs)
        return __wrapper

    def __init__(self):
        self._clients = {}
        self._current_client = None
        self.users_sync = {}

    @property
    def latest_accept_version(self):
        v = self.client_versions
        return u"v{}".format(v[len(v) - 1][0])

    @property
    def client_versions(self):
        return sorted(self.__api_versions__, key=lambda (version, klass): version)

    def accept_version(self):
        return self.latest_accept_version

    def latest_prepare_sign_request(self, *a, **kw):
        v = self.client_versions
        return self._clients[v[len(v) - 1][0]]._prepare_signed_request(*a, **kw)

    def latest_prepare_public_request(self, *a, **kw):
        v = self.client_versions
        return self._clients[v[len(v) - 1][0]]._prepare_public_request(*a, **kw)

    def init(self, url, session_pool=None, proxy_config=None, cert_bundle=None):
        self.url = url
        self.session_pool = session_pool or SessionPool()
        self.proxy_config = proxy_config
        self.cert_bundle = cert_bundle

        this = self

        class _ClientWrapper(object):
            def __init__(self, instance, wrapper):
                self._c_instance = instance
                self._c_methods = inspect.getmembers(self._c_instance, predicate=inspect.ismethod)

                # do not wrap `APIClient` inheritted internal methods, for `BACKED_CLIENT.Vx`
                resource_methods = set(
                    map(lambda (name, _): name, self._c_methods)).difference(
                        ["__init__", "put", "get", "delete", "post", "patch", "accept_version"])

                for method_name in resource_methods:
                    setattr(self, method_name, wrapper(
                        getattr(self._c_instance, method_name)))

                # set preparer methods to latest for all older client instances.
                setattr(self._c_instance, "accept_version", lambda: this.latest_accept_version)
                setattr(self._c_instance, "prepare_signed_request", this.latest_prepare_sign_request)
                setattr(self._c_instance, "prepare_public_request", this.latest_prepare_public_request)
                setattr(self, "accept_version", lambda: this.latest_accept_version)
                setattr(self, "prepare_signed_request", this.latest_prepare_sign_request)
                setattr(self, "prepare_public_request", this.latest_prepare_public_request)

        self._clients = {}
        methods = []
        for (version, klass) in self.client_versions:
            self._clients[version] = klass(
                self.url, proxy_config=self.proxy_config,
                cert_bundle=self.cert_bundle, session_pool=self.session_pool)

            c = _ClientWrapper(self._clients[version], self._handlers_wrapper)
            setattr(self, "V{}".format(version), c)
            methods = methods + c._c_methods

        self._current_client = next(client for (
            version, client) in self._clients.iteritems() if version == self.__current_version__)
        # do not wrap `APIClient` inheritted internal methods, for `BACKED_CLIENT`
        non_internal_methods = set(
            map(lambda (name, _): name, methods)).difference(["__init__", "put", "get", "delete", "post", "patch"])
        for method_name in non_internal_methods:
            setattr(self, method_name, self._handlers_wrapper(getattr(self.current_client, method_name)))

    @property
    def current_client(self):
        if not self._current_client:
            raise RuntimeError(u"init not called")
        return self._current_client