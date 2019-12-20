import os
import random
import StringIO
import struct
import sys

from .encoding import ascii_to_unicode, unicode_if_unicode_else_decode


def init_random():
    seed = struct.unpack("=I", os.urandom(4))[0]
    random.seed(seed)


def resolve_preveil_mode(mode_file_path):
    if not isinstance(mode_file_path, unicode):
        return False, None

    # Precedence
    # 0. Env[PREVEIL_MODE]
    # 1. conf/default-mode
    # 2. 'dev'
    mode = os.environ.get(u"PREVEIL_MODE")
    if mode is not None:
        mode = unicode_if_unicode_else_decode(mode)
        return True, mode

    try:
        with open(mode_file_path, u"r") as f:
            mode = f.read().strip()
        mode = ascii_to_unicode(mode)
        return True, mode
    except IOError:
        pass

    return True, u"dev"


class NotAssigned(object):
    def __init__(self):
        pass

    def __str__(self):
        return u"__NOT_ASSIGNED__"

    def serialize(self):
        return self.__str__()


def rand_unicode(length=20):
    glyphs = u"ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz"
    return u"".join(random.choice(glyphs) for _ in range(length))


def rand_str(size=1024):
    return os.urandom(size)


def rand_stream(size=1024):
    return StringIO.StringIO(rand_str(size))


# following this guideline: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/User-Agent
def make_user_agent_header(built_number, default_agent_header):
    daemon_name = ""
    if len(sys.argv) == 1:
        daemon_name = sys.argv[0].split("/")[-1]
    return u"PreVeilDesktop/{}: (daemon:{}) ({})".format(built_number, daemon_name, default_agent_header)

# custom_header = {
#     "User-Agent": makeUserAgentHeader(Config.build_version, session_cache[backend].headers["user-agent"]),
#     "X-DEVICE-METADATA": jdumps({"client_version": Config.build_version})
# }


def get_rand_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    s.listen(1)
    port = s.getsockname()[1]
    s.close()
    return port
