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
        # 0. PREVEIL_MODE
        # 1. conf/default-mode
        # 2. 'dev'
        mode = os.environ.get('PREVEIL_MODE')
        if mode is None:
            path = os.path.join(config_dir, "default-mode")
            try:
                with open(path, 'r') as f:
                    mode = f.read().strip()
            except IOError:
                mode = "dev"
        cls.mode = mode

        path = os.path.join(config_dir, "config.yaml")
        with open(path, 'r') as f:
            c = yaml.load(f.read())
            if c.has_key(mode) is False:
                raise Exception("error, exiting: PREVEIL_MODE={} unavailable at {}".format(mode, path))
        cls.data = c

        super(MetaConf, cls).__init__(name, bases, dct)
