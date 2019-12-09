import base64
import collections
import copy
import itertools
import os
import random
import StringIO
import struct
import sys
import time
import types
import urllib
import urlparse

import simplejson
import yaml

from .hook_decorators import WrapExceptions
from .params import params


DATA_DIR_MODE = 0o750


class EncodingException(Exception):
    def __init__(self, exception=u""):
        super(EncodingException, self).__init__(exception)


if sys.platform in ["darwin", "linux2"]:
    import pwd


def init_random():
    seed = struct.unpack("=I", os.urandom(4))[0]
    random.seed(seed)


def get_dir(path):
    return os.path.dirname(os.path.realpath(path))


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


def read_yaml_config(path):
    with open(path, u"r") as f:
        y = yaml.load(f.read())
    return y


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(unicode)
def unicode_to_ascii(s):
    return s.encode("ascii")


def unicode_to_ascii_with_replace(s):
    return s.encode("ascii", "replace")


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(bytes)
def ascii_to_unicode(s):
    return s.encode("utf-8").decode("utf-8")


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(unicode)
def utf8_encode(s):
    return s.encode("utf-8")


@WrapExceptions(EncodingException,
                [KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(bytes)
def utf8_decode(s):
    return s.decode("utf-8")


def unicode_if_unicode_else_decode(b):
    if isinstance(b, unicode):
        return b
    else:
        return utf8_decode(b)


def encode_content_if_unicode(content):
    if isinstance(content, unicode):
        return utf8_encode(content)
    return content


@WrapExceptions(
    EncodingException,
    [ValueError, KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(bytes, {types.NoneType, str})
def b64enc(data, altchars=None):
    enc = base64.b64encode(data, altchars=altchars)
    return ascii_to_unicode(enc)


@WrapExceptions(
    EncodingException,
    [ValueError, KeyError, TypeError, UnicodeDecodeError, UnicodeEncodeError])
@params(unicode, {types.NoneType, str})
def b64dec(data, altchars=None):
    return base64.b64decode(data, altchars=altchars)


def to_int(data):
    if not (isinstance(data, (unicode, str)) or
            isinstance(data, (int, long, float))):
        return False, None

    try:
        return True, int(data)
    except ValueError:
        return False, None


@WrapExceptions(EncodingException, [UnicodeDecodeError, UnicodeEncodeError])
def jdumps(data, ensure_ascii=False):
    return simplejson.dumps(data, ensure_ascii=ensure_ascii)


@WrapExceptions(EncodingException, [
    KeyError, TypeError, ValueError, simplejson.JSONDecodeError,
    UnicodeDecodeError, UnicodeEncodeError
])
@params(unicode)
def jloads(data):
    return simplejson.loads(data)


def jload(fp):
    if not isinstance(fp, file):
        return False, None

    try:
        return True, simplejson.load(fp)
    except (simplejson.JSONDecodeError, UnicodeDecodeError, UnicodeEncodeError,
            ValueError):
        return False, None


def get_temp_file_path(mode_dir):
    return os.path.join(
        temp_dir(mode_dir),
        "%s.%s.%s" % (time.time(), random.randint(0, 1000000), os.getpid()))


def check_running_as_root():
    if sys.platform in ["darwin", "linux2"]:
        uid = os.getuid()
        gid = os.getgid()
        if uid != os.geteuid():
            return False
        elif gid != os.getegid():
            return False
        elif uid != 0:
            return False
        elif gid != 0:
            return False
        return True
    else:
        return True


class DoAsPreVeil(object):
    def __init__(self):
        self._noop = True

    def __enter__(self):
        if sys.platform in ["darwin", "linux2"]:
            self.original_egid = os.getegid()
            self.original_euid = os.geteuid()

            preveil_pwuid = pwd.getpwnam("preveil")
            if self.original_egid == preveil_pwuid.pw_gid and   \
                    self.original_euid == preveil_pwuid.pw_uid:
                self._noop = True
                return

            try:
                # seteuid/gid fails unless process is running as `root`
                # Tests do not run as `root`
                os.setegid(preveil_pwuid.pw_gid)
                os.seteuid(preveil_pwuid.pw_uid)
                self._noop = False
            except OSError:
                pass
        else:
            pass

    def __exit__(self, type, value, traceback):
        if sys.platform in ["darwin", "linux2"]:
            if self._noop is False:
                os.setegid(self.original_egid)
                os.seteuid(self.original_euid)
        else:
            pass

        if isinstance(value, Exception):
            raise value


def switch_user_preveil():
    if sys.platform in ["darwin", "linux2"]:
        preveil_pwuid = pwd.getpwnam("preveil")
        os.setregid(preveil_pwuid.pw_gid, preveil_pwuid.pw_gid)
        os.setreuid(preveil_pwuid.pw_uid, preveil_pwuid.pw_uid)
    elif "win32" == sys.platform:
        pass


# http://stackoverflow.com/questions/3812849/how-to-check-whether-a-directory-is-a-sub-directory-of-another-directory
def is_same_dir_or_child(directory, test_child):
    directory = os.path.normpath(os.path.realpath(directory))
    test_child = os.path.normpath(os.path.realpath(test_child))
    if directory == test_child:
        return True

    # os.path.join, appending nothing adds a trailing seperator;
    # we want to avoid issues like, /a/b matching as the parent of
    # /a/bee/c
    directory = os.path.join(directory, "")

    # return true, if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([test_child, directory]) == directory


def recur_chown(path, uid, gid):
    os.chown(path, uid, gid)
    for root, dirs, files in os.walk(path):
        for name in dirs:
            os.chown(os.path.join(root, name), uid, gid)
        for name in files:
            os.chown(os.path.join(root, name), uid, gid)


def quiet_mkdir(path):
    try:
        os.mkdir(path)
    except OSError:
        if not os.path.isdir(path):
            raise


def file_no_ext(path):
    return os.path.splitext(os.path.basename(path))[0]


def daemon_data_dir(wd):
    return os.path.join(wd, "daemon")


def modes_dir(wd):
    return os.path.join(daemon_data_dir(wd), "modes")


def get_mode_dir(wd, mode):
    return os.path.join(modes_dir(wd), mode)


def logs_dir(mode_dir):
    return os.path.join(mode_dir, "logs")


def temp_dir(mode_dir):
    return os.path.join(mode_dir, "temp")


# Handle cases where /var/preveil/* doesn't exist or it has the wrong
# owner:group
#
# This function tries to provide the following guarentee, if a process returns
# successfully from init_daemon_data_dirs(), /var/preveil/* is available to it with the
# correct owner:group.  This guarentee is easier to provide if all processes
# only create these directories (or change their permissions) with this
# function.
def init_daemon_data_dirs(wd, mode, is_test=False):
    if sys.platform in ["darwin", "linux2"]:
        mask = os.umask(0o777)
        os.umask(mask)
        if (DATA_DIR_MODE & (~mask)) != DATA_DIR_MODE:
            raise Exception("bad umask: %s" % mask)
    else:
        pass

    quiet_mkdir(wd)
    quiet_mkdir(daemon_data_dir(wd))
    quiet_mkdir(modes_dir(wd))
    mode_dir = get_mode_dir(wd, mode)
    quiet_mkdir(mode_dir)
    quiet_mkdir(logs_dir(mode_dir))
    quiet_mkdir(temp_dir(mode_dir))

    if not is_test:
        if sys.platform in ["darwin", "linux2"]:
            preveil_pwuid = pwd.getpwnam("preveil")
            preveil_uid = preveil_pwuid.pw_uid
            preveil_gid = preveil_pwuid.pw_gid
            recur_chown(wd, preveil_uid, preveil_gid)
        else:
            pass

    return mode_dir


class CaseInsensitiveSet(collections.Set):
    def __init__(self, lyst):
        self.data = CaseInsensitiveDict()
        for e in lyst:
            self.data[e] = e

    def __contains__(self, item):
        return item in self.data

    def __iter__(self):
        for _, n in self.data.iteritems():
            yield n

    def __len__(self):
        return len(self.data)

    def union(self, other):
        if not isinstance(other, list):
            raise TypeError(u"other must be of type list")

        new = CaseInsensitiveDict(copy.deepcopy(self.data))
        for o in other:
            new[o] = o

        return CaseInsensitiveSet(new.values())

    def difference(self, other):
        if not isinstance(other, list):
            raise TypeError(u"other must be of type list")
        new = CaseInsensitiveDict(copy.deepcopy(self.data))
        for o in other:
            if o in new:
                del new[o]

        return CaseInsensitiveSet(new.values())


# Lifted from m000 @ http://stackoverflow.com/a/32888599
class CaseInsensitiveDict(dict):
    @classmethod
    def _k(cls, key):
        if isinstance(key, basestring):
            return key.lower()
        elif isinstance(key, tuple):
            return tuple([cls._k(i) for i in key])
        else:
            return key

    def __init__(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        self._convert_keys()

    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(self.__class__._k(key))

    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(self.__class__._k(key), value)

    def __delitem__(self, key):
        return super(CaseInsensitiveDict, self).__delitem__(self.__class__._k(key))

    def __contains__(self, key):
        return super(CaseInsensitiveDict, self).__contains__(self.__class__._k(key))

    def has_key(self, key):
        return self.__class__._k(key) in super(CaseInsensitiveDict, self)

    def pop(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).pop(self.__class__._k(key), *args, **kwargs)

    def get(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).get(self.__class__._k(key), *args, **kwargs)

    def setdefault(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).setdefault(self.__class__._k(key), *args, **kwargs)

    def update(self, e={}, **f):
        super(CaseInsensitiveDict, self).update(self.__class__(e))
        super(CaseInsensitiveDict, self).update(self.__class__(**f))

    def _convert_keys(self):
        for k in list(self.keys()):
            v = super(CaseInsensitiveDict, self).pop(k)
            self.__setitem__(k, v)


class NotAssigned(object):
    def __init__(self):
        pass

    def __str__(self):
        return u"__NOT_ASSIGNED__"

    def serialize(self):
        return self.__str__()


def merge_dicts(*args):
    ret = {}
    for _dict in args:
        if not isinstance(_dict, dict):
            raise TypeError(u"merge_dicts: Arguments must be of type dict")
        ret.update(_dict)
    return ret


def rand_unicode(length=20):
    glyphs = u"ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890abcdefghijklmnopqrstuvwxyz"
    return u"".join(random.choice(glyphs) for _ in range(length))


def rand_str(size=1024):
    return os.urandom(size)


def rand_stream(size=1024):
    return StringIO.StringIO(rand_str(size))


# https://docs.python.org/dev/library/itertools.html#itertools-recipes
def partition(pred, iterable):
    'Use a predicate to partition entries into false entries and true entries'
    # partition(is_odd, range(10)) --> 0 2 4 6 8   and  1 3 5 7 9
    t1, t2 = itertools.tee(iterable)
    return filter(pred, t2), filter(lambda x: not pred(x), t1)


def parse_file_uri(path):
    """
        Process the given path url to determine the scheme.
        :return: required_download, processed_url
    """
    p = urlparse.urlparse(path)

    if p.scheme in ["https", "http"]:
        return True, path
    elif p.scheme == "file":
        # url to path name, i.e: convert %20 to space
        path = urllib.url2pathname(p.path)
        return False, os.path.abspath(os.path.join(p.netloc, path))
    else:
        # treat as a local file
        return False, urllib.unquote(path)


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
