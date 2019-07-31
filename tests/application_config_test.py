import pytest
import requests

from pvHelpers import ApplicationConfig

def test_init_config():
    replica = ApplicationConfig()
    assert replica.initialized == False
    with pytest.raises(ValueError):
        replica.initConfig()

    # test init via mode
    for m in [u"prod", u"staging", u"dev", u"test", u"test2", u"ansible_local_test", u"ansible_local_test2"]:
        replica.initConfig(mode=m)