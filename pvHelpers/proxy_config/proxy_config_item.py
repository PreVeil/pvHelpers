from .constants import IPProtocol
from requests.auth import HTTPProxyAuth
from .pac_parser import Pac

from ..misc import g_log


class ProxyPac(object):
    def __init__(self, pac_url, username=None, password=None):
        self.pac_url = pac_url
        if username is not None and password is not None:
            self.__proxy_auth = HTTPProxyAuth(username, password)
        else:
            self.__proxy_auth = None
        self.__initProxyResolver()

    def __eq__(self, other):
        if not isinstance(other, ProxyPac):
            return False

        for attr in self.__dict__:
            if self.__dict__[attr] != other.__dict__[attr]:
                return False
        return True

    def __initProxyResolver(self):
        try:
            self.__proxy_resolver = Pac(
                self.pac_url, proxy_auth=self.__proxy_auth)

        except IOError as e:
            g_log.error(u"__initProxyResolver: {}".format(e))
            self.__proxy_resolver = None

    def setBasicAuthCred(self, cred):
        if self.__proxy_resolver is not None:
            self.__proxy_auth = cred
            self.__proxy_resolver.proxy_auth = cred

    def getProxies(self, url):
        if self.__proxy_resolver is None:
            return None
        # should we open a process to avoid js crash?
        # hasn't happened for pacparser
        try:
            return self.__proxy_resolver.getProxies(url)
        except Exception as e:
            g_log.debug("ProxyResolver.getProxies {}".format(e))
            return None

    def __ne__(self, other):
        return not self == other

    def toDB(self):
        return {"pac_url": self.pac_url}

    def toBrowser(self):
        return self.toDB()

    @classmethod
    def fromDB(cls, data_dict):
        return cls(data_dict["pac_url"])


class ProxyUrl(object):
    def __init__(self, protocol, ip, port, username=None, password=None):
        # this protocol is the requests protocol that the proxy handles
        self.protocol = protocol
        self.ip = ip
        self.port = port
        self.__username = username
        self.__password = password

    def __eq__(self, other):
        if not isinstance(other, ProxyUrl):
            return False

        for attr in self.__dict__:
            if self.__dict__[attr] != other.__dict__[attr]:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def setBasicAuthCred(self, cred):
        self.__username = cred.username
        self.__password = cred.password

    # I can't find much details on determining whether the proxy handling
    # the given protocol is itself an http or https proxy
    # pypac assumes it is http
    @property
    def to_proxy_url(self):
        if self.__username is None and self.__password is None:
            return "http://{}:{}".format(self.ip, self.port)
        else:
            return "http://{}:{}@{}:{}".format(self.__username, self.__password, self.ip, self.port)

    def toBrowser(self):
        return self.toDB()

    def toDB(self):
        return {
            "protocol": self.protocol,
            "ip": self.ip,
            "port": self.port,
            "username": self.__username,
            "password": self.__password
        }

    @classmethod
    def fromDB(cls, request_dict):
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

    def addOrUpdate(self, type_, proxy_obj):
        if type_ in ProxyConfigItem.PROTOCOL_TYPES:
            self.proxies[type_] = proxy_obj

    def toDB(self):
        return {k: v.toDB() for k, v in self.proxies.iteritems()}

    def toBrowser(self):
        return self.toDB()

    @classmethod
    def fromDB(cls, data_dict):
        proxies = {}
        for k, v in data_dict.iteritems():
            if k not in ProxyConfigItem.PROTOCOL_TYPES:
                raise ValueError(
                    u"{} is not a supported proxy protocol type".format(k))

            if k in [IPProtocol.HTTP, IPProtocol.HTTPS]:
                proxies[k] = ProxyUrl.fromDB(v)
            elif k == IPProtocol.PAC:
                proxies[k] = ProxyPac.fromDB(v)
        return cls(proxies)

    def setBasicAuthCred(self, basic_proxy_auth):
        for protocol in self.proxies:
            self.proxies[protocol].setBasicAuthCred(basic_proxy_auth)

    def getProxies(self, url=None):
        if IPProtocol.PAC in self.proxies:
            if url is None:
                raise ValueError(
                    u"Must provide url to get proxies from pac file")
            return self.proxies[IPProtocol.PAC].getProxies(url)

        proxies_for_requests = []
        for k, v in self.proxies.iteritems():
            if k in [IPProtocol.HTTP, IPProtocol.HTTPS]:
                proxies_for_requests.append({
                    k: v.to_proxy_url
                })

        return proxies_for_requests if len(proxies_for_requests) > 0 else None

    @property
    def size(self):
        return len(self.proxies)
