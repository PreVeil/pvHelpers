import os
import re
import sys

from pvHelpers.application_config import ApplicationConfig
from pvHelpers.utils import rand_unicode, read_yaml_file
import pytest
import requests

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
    assert master.initialized is False

    # should raise KeyError for missing enviroment variables
    org_env, mocked_vars = os.environ, []
    while len(master.config_keys) - len(mocked_vars) > 0:
        with pytest.raises(KeyError):
            master.init_config()
        mocked_vars.append(master.config_keys[len(mocked_vars)])
        os.environ.update(
            {k.replace("-", "_").upper() if k != "mode" else "PREVEIL_MODE": str(rand_unicode(5)) for k in mocked_vars})

    # should just go through when all the required keys are in env
    master.init_config()
    os.environ = org_env

    master = MasterConfig()
    assert master.initialized is False
    # should raise for not having `config_file`
    with pytest.raises(ValueError):
        master.init_config(mode=u"dev")

    # should raise for not having `dev` mode in `config_file`
    with pytest.raises(ValueError):
        master.init_config(mode=u"dev", config_file=TEST_CONFIG_PATH)

    master.init_config(mode=u"test", config_file=TEST_CONFIG_PATH)

    assert master.initialized

    confs = read_yaml_file(TEST_CONFIG_PATH)
    confs = confs["test"]
    for k in set(master.config_keys) - set(["mode", "working-dir", "root-dir"]):
        assert confs[k] == master.get_config_by_key(k)

    assert master.get_config_by_key("mode") == "test"
    expected_root = unicode(os.path.join(os.getenv("SystemDrive") + "\\", "PreVeilData")) if \
        sys.platform == "win32" else \
        unicode(os.path.join("/", "var", "preveil"))
    assert master.get_config_by_key("root-dir") == expected_root
    assert master.get_config_by_key("working-dir") == os.path.join(expected_root, "daemon", "modes", "test")


def test_replica_init_config(requests_mock):
    master_port = 1234
    replica = ReplicaConfig()
    assert replica.initialized is False

    # mock requests
    requests_mock.register_uri(
        "PUT",
        re.compile("http://127.0.0.1:{}/get/config/*".format(master_port)),
        text="""{"value": "dummy"}"""
    )
    replica.init_config(master_port=master_port)

    for k in replica.config_keys:
        assert "dummy" == replica.get_config_by_key(k)

    # let's emulate timeout for on of the required keys
    requests_mock.register_uri(
        "PUT",
        re.compile("http://127.0.0.1:{}/get/config/working-dir".format(master_port)),
        exc=requests.exceptions.ConnectTimeout
    )

    replica = ReplicaConfig()
    replica.MAX_ATTEMPT_COUNT = 2
    with pytest.raises(ValueError):
        replica.init_config(master_port=master_port)


@pytest.mark.skip(reason="TODO")
def test_master_replicas_integration():
    pass
