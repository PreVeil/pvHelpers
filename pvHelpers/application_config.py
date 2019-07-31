
import types, os, requests, time, random
from requests.exceptions import ConnectTimeout, ConnectionError, ReadTimeout
from .params import params
from .misc import HTTP_TIMEOUT, readYAMLConfig, g_log


def fetchConfigFromMaster(master_port, key):
    resp = requests.put(
        u"http://127.0.0.1:{}/get/config/{}".format(master_port, key),
        timeout=HTTP_TIMEOUT, allow_redirects=False
    )
    resp.raise_for_status()
    return resp.json()["value"]

MAX_ATTEMPT_COUNT = 20
MIN_WAIT_TIME = 2
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
    def initConfig(self, master_port=None, config_file=None, mode=None):
        if self.initialized:
            return

        if master_port is None and (mode is None or config_file is None):
            raise ValueError(u"Process needs to be initialized either as `Master` or `Replica`")

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


        # replica instances
        if master_port:
            self.master_port = master_port
            def _fetchConfigFromMaster():
                fetched_mode = fetchConfigFromMaster(master_port, u"mode")
                for k in self.config_keys:
                    self.__config__[k] = fetchConfigFromMaster(master_port, k)

            attempt_count = 0
            while attempt_count < MAX_ATTEMPT_COUNT:
                try:
                    _fetchConfigFromMaster()
                except (ConnectionError, ConnectTimeout, ReadTimeout) as e:
                    g_log.exception(e)
                    attempt_count = attempt_count + 1
                    time.sleep(random.randrange(MIN_WAIT_TIME, MAX_WAIT_TIME))
                else:
                    break

        # master instance
        else:
            if config_file:
                status, confs = readYAMLConfig(config_file)
                if not status:
                    raise ValueError(u"failed reading provided config_file: {}".format(config_file))


        # assert initialization of all the expected `config_keys`
        if len((set(self.config_keys) - set(self.__config__))) != 0:
            raise ValueError(u"Process could not initialize all the configs! missing keys: {}".format(list(set(self.config_keys) - set(self.__config__))))

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
