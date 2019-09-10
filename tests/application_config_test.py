import os
import re
import sys

import pytest
import requests
from pvHelpers import ApplicationConfig, readYAMLConfig

TEST_CONFIG_PATH = unicode(os.path.join(os.path.dirname(__file__), "test_config.yaml"))

class MasterConfig(ApplicationConfig):
    def __init__(self):
        super(MasterConfig, self).__init__()

    @property
    def config_keys(self):
        return [
            "mode", "update-delta", "invites", "backend", "ws-backend",
            "remote-webapp-url", "uidvalidity", "reset-tables", "mail-db-version",
            "actions-db-version", "imap-port", "smtp-port", "crypto-port", "local-webapp-port",
            "filesync-port", "root-dir", "working-dir", "feature-flags-enabled"
        ]

class ReplicaConfig(ApplicationConfig):
    def __init__(self):
        super(ReplicaConfig, self).__init__()

    @property
    def config_keys(self):
        return [
            "mode", "update-delta", "invites", "backend", "ws-backend",
            "remote-webapp-url", "uidvalidity", "reset-tables", "mail-db-version",
            "actions-db-version", "imap-port", "smtp-port", "crypto-port", "local-webapp-port",
            "filesync-port", "root-dir", "working-dir", "feature-flags-enabled"
        ]

def test_master_init_config():
    master = MasterConfig()
    assert master.initialized == False

    # should raise KeyError for missing enviroment variables
    with pytest.raises(KeyError):
        master.initConfig()


    # should raise for not having `config_file`
    with pytest.raises(ValueError):
        master.initConfig(mode=u"dev")

    # should raise for not having `dev` mode in `config_file`
    with pytest.raises(ValueError):
        master.initConfig(mode=u"dev", config_file=TEST_CONFIG_PATH)

    master.initConfig(mode=u"test", config_file=TEST_CONFIG_PATH)

    assert master.initialized == True

    status, confs = readYAMLConfig(TEST_CONFIG_PATH)
    assert status
    confs =  confs["test"]
    for k in set(master.config_keys) - set(["mode", "working-dir", "root-dir"]):
        assert confs[k] == master.getConfigByKey(k)

    assert master.getConfigByKey("mode") == "test"
    expected_root = unicode(os.path.join(os.getenv("SystemDrive") + "\\", "PreVeilData")) \
                    if sys.platform == "win32" \
                    else unicode(os.path.join("/", "var", "preveil"))
    assert master.getConfigByKey("root-dir") ==  expected_root
    assert master.getConfigByKey("working-dir") == os.path.join(expected_root, "daemon", "modes", "test")


def test_replica_init_config(requests_mock):
    master_port = 1234
    replica = ReplicaConfig()
    assert replica.initialized == False

    # mock requests
    requests_mock.register_uri(
        "PUT",
        re.compile("http://127.0.0.1:{}/get/config/*".format(master_port)),
        text="""{"value": "dummy"}"""
    )
    replica.initConfig(master_port=master_port)

    for k in replica.config_keys:
        assert "dummy" == replica.getConfigByKey(k)

    # let's emulate timeout for on of the required keys
    requests_mock.register_uri(
        "PUT",
        re.compile("http://127.0.0.1:{}/get/config/working-dir".format(master_port)),
        exc=requests.exceptions.ConnectTimeout
    )

    replica = ReplicaConfig()
    replica.MAX_ATTEMPT_COUNT = 2
    with pytest.raises(ValueError):
        replica.initConfig(master_port=master_port)

@pytest.mark.skip(reason="TODO")
def test_master_replicas_integration():
    pass
