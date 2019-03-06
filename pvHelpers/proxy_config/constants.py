class IPProtocol():
    HTTP = "http"
    HTTPS = "https"
    PAC = "pac"


class ProxyKey():
    # darwin
    HTTPEnable = "HTTPEnable"
    HTTPSEnable = "HTTPSEnable"
    HTTPPort = "HTTPPort"
    HTTPSPort = "HTTPSPort"
    HTTPProxy = "HTTPProxy"
    HTTPSProxy = "HTTPSProxy"
    ProxyAutoConfigEnable = "ProxyAutoConfigEnable"
    ProxyAutoConfigURLString = "ProxyAutoConfigURLString"

    # win32
    ProxyEnable = "ProxyEnable"
    ProxyServer = "ProxyServer"
    AutoConfigURL = "AutoConfigURL"

    # common
    OS_PROXY_SETTINGS = "OS_PROXY_SETTINGS"
    MANUAL_PROXY_SETTINGS = "MANUAL_PROXY_SETTINGS"
    PROXY_BASIC_AUTH = "PROXY_BASIC_AUTH"
