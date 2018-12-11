
import types, os, requests, time, random
from requests.exceptions import ConnectTimeout, ConnectionError, ReadTimeout
from .params import params
from .misc import HTTP_TIMEOUT


def fetchConfigFromMaster(master_port, key):
    resp = requests.put(
        u"http://127.0.0.1:{}/get/config/{}".format(master_port, key),
        timeout=HTTP_TIMEOUT, allow_redirects=False
    )
    resp.raise_for_status()
    return resp.json()["value"]

MAX_ATTEMPT_COUNT = 10
MAX_WAIT_TIME = 4

class ApplicationConfig(object):
    __config__ = {}
    def __init__(self):
        self.initialized = False
        self.mode = None

    # HACK: This is a dirty, but quick to just make sure a Config instance won't be used without being initialized
    def __getattribute__(self, attr):
        if attr not in ["initConfig", "config_keys", "initialized", "__config__"] and not self.initialized:
            raise RuntimeError(u"Config not initialized!")

        return object.__getattribute__(self, attr)

    @params(object, {types.NoneType, int}, {types.NoneType, unicode})
    def initConfig(self, master_port=None, mode=None):
        if self.initialized:
            return

        if master_port is None and mode is None:
            raise ValueError(u"Process needs to be initialized either as `MASTER` or `Replica`")

        if mode:
            self.mode = mode
            # HACK: just a work around for current installation method
            # ideally, `MASTER_PORT` should be provided on process invocation
            if mode == u"prod":
                 master_port = 4002
            elif mode == u"staging":
                master_port = 6002
            elif mode in [u"test2_dkr", u"ansible_local_test2", u"test2"]:
                master_port = 2012
            elif mode in ["ansible_local_test", "dev", "test"]:
                master_port = 2002
            else:
                for k in self.config_keys:
                    self.__config__[k] = os.environ[k.replace("-", "_").upper()]


        if master_port:
            self.master_port = master_port
            def _fetchConfigFromMaster():
                self.mode = fetchConfigFromMaster(master_port, u"mode")
                for k in self.config_keys:
                    self.__config__[k] = fetchConfigFromMaster(master_port, k)

            attempt_count = 0
            while attempt_count < MAX_ATTEMPT_COUNT:
                try:
                    _fetchConfigFromMaster()
                except (ConnectionError, ConnectTimeout, ReadTimeout) as e:
                    print e
                    attempt_count = attempt_count + 1
                    time.sleep(random.randrange(1, MAX_WAIT_TIME))
                else:
                    break

        self.initialized = True


    @property
    def config_keys(self):
        raise NotImplementedError()

    def getConfigByKey(self, key):
        return self.__config__[key]

    def isTestMode(self):
        return self.mode.startswith(u"test") or self.mode in ["ansible_local_test", "ansible_local_test2"]

    def isProdMode(self):
        return self.mode == u"prod"

    def isDevMode(self):
        return self.mode == u"dev"
