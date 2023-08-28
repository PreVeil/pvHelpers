from .constants import IPProtocol
from .pac_parser import Pac

from ..log import g_log


class ProxyPac(object):
    def __init__(self, pac_url, proxy_auth=None):
        self.pac_url = pac_url
        self.__proxy_auth = proxy_auth
        self.__proxy_resolver = Pac(self.pac_url, proxy_auth=self.__proxy_auth)

    def __del__(self):
        self.__proxy_resolver.clean_up()

    def __eq__(self, other):
        if not isinstance(other, ProxyPac):
            return False

        for attr in self.__dict__:
            if self.__dict__[attr] != other.__dict__[attr]:
                return False
        return True

    def set_basic_auth_cred(self, cred):
        self.__proxy_auth = cred
        self.__proxy_resolver.proxy_auth = cred

    def get_proxies(self, url):
        # should we open a process to avoid js crash?
        # hasn't happened for pacparser
        try:
            return self.__proxy_resolver.get_proxies(url)
        except Exception as e:
            g_log.debug("ProxyResolver.get_proxies {}".format(e))
            self.__proxy_resolver.clean_up()
            return None

    def __ne__(self, other):
        return not self == other

    def toDict(self):
        return {"protocol": IPProtocol.PAC, "pac_url": self.pac_url}

    @classmethod
    def fromDict(cls, data_dict):
        return cls(data_dict["pac_url"])


class ProxyUrl(object):
    def __init__(self, protocol, ip, port, username=None, password=None):
        # this protocol is the requests protocol that the proxy handles
        self.protocol = protocol
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    def __eq__(self, other):
        if not isinstance(other, ProxyUrl):
            return False

        for attr in self.__dict__:
            if self.__dict__[attr] != other.__dict__[attr]:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def set_basic_auth_cred(self, cred):
        self.username = cred.username
        self.password = cred.password

    # I can't find much details on determining whether the proxy handling
    # the given protocol is itself an http or https proxy
    # pypac assumes it is http
    @property
    def to_proxy_url(self):
        if self.username is None and self.password is None:
            return "http://{}:{}".format(self.ip, self.port)
        else:
            return "http://{}:{}@{}:{}".format(self.username, self.password,
                                               self.ip, self.port)

    def toDict(self):
        return {
            "protocol": self.protocol,
            "ip": self.ip,
            "port": self.port,
            "username": self.username,
            "password": self.password
        }

    @classmethod
    def fromDict(cls, request_dict):
        return cls(
            request_dict["protocol"],
            request_dict["ip"],
            request_dict["port"],
            request_dict["username"],
            request_dict["password"],
        )


class ProxyConfigItem(object):

    PROTOCOL_TYPES = [IPProtocol.HTTP, IPProtocol.HTTPS, IPProtocol.PAC]

    def __init__(self, proxies=None):
        self.proxies = {} if proxies is None else proxies

    def __eq__(self, other):
        if not isinstance(other, ProxyConfigItem):
            return False

        if self.size != other.size:
            return False

        for type_ in self.proxies:
            if self.proxies[type_] != other.proxies.get(type_):
                return False

        return True

    def __ne__(self, other):
        return not self == other

    def add_or_update(self, type_, proxy_obj):
        if type_ in ProxyConfigItem.PROTOCOL_TYPES:
            if type_ == IPProtocol.PAC and type_ in self.proxies:
                # clean up current pac parser js engine
                del self.proxies[type_]
            self.proxies[type_] = proxy_obj

    # need this to work with the existing temp object interface
    def toDB(self):
        return self.toDict()

    def toDict(self):
        return {k: v.toDict() for k, v in self.proxies.iteritems()}

    @classmethod
    def fromDict(cls, data_dict):
        proxies = {}
        for k, v in data_dict.iteritems():
            if k not in ProxyConfigItem.PROTOCOL_TYPES:
                raise ValueError(
                    u"{} is not a supported proxy protocol type".format(k))

            if k in [IPProtocol.HTTP, IPProtocol.HTTPS]:
                proxies[k] = ProxyUrl.fromDict(v)
            elif k == IPProtocol.PAC:
                proxies[k] = ProxyPac.fromDict(v)
        return cls(proxies)

    def set_basic_auth_cred(self, basic_proxy_auth):
        for protocol in self.proxies:
            self.proxies[protocol].set_basic_auth_cred(basic_proxy_auth)

    def get_proxies(self, url):
        if IPProtocol.PAC in self.proxies:
            return self.proxies[IPProtocol.PAC].get_proxies(url)

        proxies_for_requests = {
            k: v.to_proxy_url
            for k, v in self.proxies.iteritems()
        }
        if len(proxies_for_requests) > 0:
            return [proxies_for_requests]

        return None

    @property
    def size(self):
        return len(self.proxies)
