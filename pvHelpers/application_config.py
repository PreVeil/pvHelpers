
from __future__ import absolute_import
import os
import random
import sys
import time
import types

import requests
from pvHelpers import HTTP_TIMEOUT, g_log, getModeDir, params, readYAMLConfig
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout
import six


def fetchConfigFromMaster(master_port, key):
    resp = requests.put(
        u"http://127.0.0.1:{}/get/config/{}".format(master_port, key),
        timeout=HTTP_TIMEOUT, allow_redirects=False
    )
    resp.raise_for_status()
    return resp.json()["value"]


class ApplicationConfig(object):
    MAX_ATTEMPT_COUNT = 20
    MIN_WAIT_TIME = 2
    MAX_WAIT_TIME = 4

    def __init__(self):
        self.initialized = False
        self.__config__ = {}

    # HACK: This is a dirty, but quick to just make sure a Config instance won't be used without being initialized
    def __getattribute__(self, attr):
        if attr not in ["initConfig", "config_keys", "initialized", "__config__", "MAX_ATTEMPT_COUNT", "MIN_WAIT_TIME", "MAX_WAIT_TIME"] and not self.initialized:
            raise RuntimeError(u"Config not initialized!")

        return object.__getattribute__(self, attr)

    @params(object, {type(None), int}, {type(None), six.text_type}, {type(None), six.text_type})
    def initConfig(self, master_port=None, config_file=None, mode=None):
        if self.initialized:
            return

        # master instance
        if mode:
            if not config_file:
                raise ValueError(u"missing config file")
            status, confs = readYAMLConfig(config_file)
            if not status:
                raise ValueError(u"failed reading provided config_file: {}".format(config_file))

            if mode not in confs:
                raise ValueError("config file missing mode {}".format(mode))

            for (key, value) in six.iteritems(confs[mode]):
                self.__config__[key] = value

            self.__config__["mode"] = mode

            if sys.platform in ["darwin", "linux2"]:
                self.__config__["root-dir"] = six.text_type(os.path.join("/", "var", "preveil"))
            elif "win32" == sys.platform:
                self.__config__["root-dir"] = six.text_type(os.path.join(os.getenv("SystemDrive") + "\\", "PreVeilData"))
            else:
                raise NotImplementedError("unsupported platform {}".format(sys.platform))

            # HACK: distinction between `ROOT_DIR` and `WORKING_DIR` is unfortunate
            # ideally, each process's `working _dir` path shouldn't be dependent on
            # what `mode` it's running in. we can deal w this later when we have a
            # reliable updater that could safely change these fixed structures
            self.__config__["working-dir"] = six.text_type(getModeDir(self.__config__["root-dir"], self.__config__["mode"]))

        # replica instances
        elif master_port:
            self.master_port = master_port
            def _fetchConfigFromMaster():
                self.__config__["mode"] = fetchConfigFromMaster(master_port, u"mode")
                for k in self.config_keys:
                    self.__config__[k] = fetchConfigFromMaster(master_port, k)

            attempt_count = 0
            while attempt_count < self.MAX_ATTEMPT_COUNT:
                try:
                    _fetchConfigFromMaster()
                except (ConnectionError, ConnectTimeout, ReadTimeout) as e:
                    g_log.exception(e)
                    attempt_count = attempt_count + 1
                    time.sleep(random.randrange(self.MIN_WAIT_TIME, self.MAX_WAIT_TIME))
                else:
                    break

        else:
            for k in self.config_keys:
                env_key = "PREVEIL_MODE" if k == "mode" else k.replace("-", "_").upper()
                self.__config__[k] = os.environ[env_key]


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
        return self.getConfigByKey("mode").startswith(u"test") or self.getConfigByKey("mode") in ["ansible_local_test", "ansible_local_test2"]

    def isProdMode(self):
        return self.getConfigByKey("mode") == u"prod"

    def isDevMode(self):
        return self.getConfigByKey("mode") == u"dev"
