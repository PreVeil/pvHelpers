import os
import yaml
import sys

def getdir(path):
    return os.path.dirname(os.path.realpath(path))

# XXX: what's the right way to deal with backwards/forwards compatability?
class MetaConf(type):
    def __init__(cls, name, bases, dct):
        config_dir = dct["config_dir"]

        # Precedence
        # 0. Env
        # 1. PREVEIL_MODE
        # 2. conf/default-mode
        # 3. 'dev'
        mode = os.environ.get('PREVEIL_MODE')
        if mode is None:
            path = os.path.join(config_dir, "default-mode")
            try:
                with open(path, 'r') as f:
                    mode = f.read().strip()
            except IOError:
                mode = "dev"
        cls.mode = mode
        cls.data = {}

        try:
            path = os.path.join(config_dir, "config.yaml")
            with open(path, 'r') as f:
                c = yaml.load(f.read())
                if c.has_key(mode) is False:
                    raise Exception("error, exiting: PREVEIL_MODE={} unavailable at {}".format(mode, path))
            cls.data = c
        except IOError:
            pass

        cls.path = path

        super(MetaConf, cls).__init__(name, bases, dct)

    def _getValue(cls, key, override_mode=None):
        value = os.environ.get(key)
        if value is not None:
            return value

        if override_mode is None:
            override_mode = cls.mode

        if cls.data.has_key(override_mode) == False:
            raise Exception("error, exiting: PREVEIL_MODE={} unavailable at {} for key {}".format(override_mode, cls.path, key))
        value = cls.data[override_mode][key]

        return value
