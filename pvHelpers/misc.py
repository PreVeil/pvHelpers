import os
import yaml
import sys
import random
import time
import simplejson
import datetime
import base64
import twisted.python.log
import logging
import logging.handlers
import flanker.mime
import sqlite3

if "darwin" == sys.platform:
    import pwd
    import grp

DATA_DIR_MODE = 0o750
HTTP_TIMEOUT = 15

def getdir(path):
    return os.path.dirname(os.path.realpath(path))

class MetaConf(type):
    @staticmethod
    def determineCurrentMode():
        # Precedence
        # 0. Env[PREVEIL_MODE]
        # 1. 'dev'
        status, mode = unicodeIfUnicodeElseDecode(os.environ.get('PREVEIL_MODE', u'dev'))
        if status == False:
            raise Exception("error, determineCurrentMode failed")

        return mode

    def __init__(cls, name, bases, dct):
        cls.mode = MetaConf.determineCurrentMode()
        cls.data = {}

        config_dir = dct["config_dir"]

        try:
            path = os.path.join(config_dir, "config.yaml")
            with open(path, 'r') as f:
                c = yaml.load(f.read())
                if c.has_key(cls.mode) is False:
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

class LogWrapper:
    def __init__(self):
        self.logobj = None

    def updateLog(self, logobj):
        self.logobj = logobj

    def debug(self, string):
        if self.logobj is not None:
            self.logobj.debug(string)
        else:
            print "{} DEBUG: {}".format(self.__now(), string)

    def info(self, string):
        if self.logobj is not None:
            self.logobj.info(string)
        else:
            print "{} INFO: {}".format(self.__now(), string)

    def warning(self, string):
        if self.logobj is not None:
            self.logobj.warning(string)
        else:
            print "{} WARN: {}".format(self.__now(), string)

    warn=warning

    def error(self, string):
        if self.logobj is not None:
            self.logobj.error(string)
        else:
            print "{} ERROR: {}".format(self.__now(), string)

    def __now(self):
        return datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    # We don't start file system writes from the constructor because they
    # depend on the PreVeil directory structure.  Once we've confirmed
    # the PreVeil directories exist, we can start logging to disk instead of
    # stdout.
    def startFileSystemWrites(self, name, extra_logger=None):
        logobj = logging.getLogger(name)
        logobj.setLevel(logging.DEBUG)

        logpath = os.path.join(logsDir(), "{}.log".format(name))
        # TimedRotatingFileHandler will only rotate the logs if the process is
        # running at midnight (assuming a log per day). This means that
        # clients who put their computer to sleep at night will never get a log
        # rotation.  Just use RotatingFileHandler so we can avoid exploded logs.
        handler   = logging.handlers.RotatingFileHandler(logpath, maxBytes=1000000, backupCount=1000)
        formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s,%(lineno)d]: %(message)s')
        handler.setFormatter(formatter)
        logobj.addHandler(handler)

        if extra_logger is not None:
            extra_logger.addHandler(handler)

        observer = twisted.python.log.PythonLoggingObserver(loggerName=name)
        observer.start()

        self.logobj = logobj

def unicodeToASCII(s):
    if not isinstance(s, unicode):
        return False, None

    try:
        return True, s.encode('ascii')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False, False

def unicodeToASCIIWithReplace(s):
    return s.encode('ascii', 'replace')

def ASCIIToUnicode(s):
    if not isinstance(s, str):
        return False, None

    try:
        return True, s.encode('utf-8').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False, False

def utf8Encode(s):
    if not isinstance(s, unicode):
        return False, None

    try:
        return True, s.encode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False, False

def utf8Decode(s):
    if not (isinstance(s, str) or isinstance(s, bytes)):
        return False, None

    try:
        return True, s.decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False, False

def unicodeIfUnicodeElseDecode(b):
    if isinstance(b, unicode):
        return True, b
    else:
        return utf8Decode(b)

# binary -> unicode
def b64enc(data, altchars=None):
    if not (isinstance(data, bytes) or isinstance(data, str)):
        return False, None

    enc = base64.b64encode(data, altchars=altchars)
    return ASCIIToUnicode(enc)

# unicode -> binary
def b64dec(data, altchars=None):
    if not isinstance(data, unicode):
        return False, None

    try:
        return True, base64.b64decode(data, altchars=altchars)
    except TypeError:
        return False, None

def toInt(data):
    if not (isinstance(data, unicode) or (isinstance(data, (int, long, float)))):
        return False, None

    try:
        return True, int(data)
    except ValueError:
        return False, None

def jdumps(data, ensure_ascii=False):
    return simplejson.dumps(data, ensure_ascii=ensure_ascii)

def jloads(data):
    if not isinstance(data, unicode):
        return False, None

    try:
        return True, simplejson.loads(data)
    except (simplejson.JSONDecodeError, UnicodeDecodeError, UnicodeEncodeError, ValueError):
        return False, None

def jload(fp):
    if not isinstance(fp, file):
        return False, None

    try:
        return True, simplejson.load(fp)
    except (simplejson.JSONDecodeError, UnicodeDecodeError, UnicodeEncodeError, ValueError):
        return False, None

def filesystemSafeBase64Encode(email):
    return b64enc(email.upper(), "()")

def getTempFilePath():
    return os.path.join(tempDir(),
        "%s.%s.%s" % (time.time(), random.randint(0, 1000000), os.getpid()))

def getBodyFromFlankerMessage(message):
    if message.content_type.is_singlepart():
        return message._container.read_body()
    else:
        assert message.content_type.is_multipart()

        # HACK: Print message text without the headers
        tmp = flanker.mime.from_string(message.to_string())
        tmp.remove_headers(*tmp.headers.keys())
        return tmp.to_string()

# FIXME: Don't use logRaise()
def checkRunningAsRoot():
    if "darwin" == sys.platform:
        uid = os.getuid()
        gid = os.getgid()
        if uid != os.geteuid():
            logRaise("ruid must match euid")
        elif gid != os.getegid():
            logRaise("rgid must match egid")
        elif uid != 0 or pwd.getpwuid(uid).pw_name != "root":
            logRaise("all servers must be started with uid=0 (root)")
        elif gid != 0 or grp.getgrgid(gid).gr_name != "wheel":
            logRaise("all servers must be started with gid=0 (wheel)")
    elif "win32" == sys.platform:
        pass

class DoAsPreVeil:
    def __init__(self):
        pass

    def __enter__(self):
        if "darwin" == sys.platform:
            self.original_egid = os.getegid()
            self.original_euid = os.geteuid()

            preveil_pwuid = pwd.getpwnam("preveil")
            if self.original_egid == preveil_pwuid.pw_gid and   \
                    self.original_euid == preveil_pwuid.pw_uid:
                self.noop = True
                return

            self.noop = False
            os.setegid(preveil_pwuid.pw_gid)
            os.seteuid(preveil_pwuid.pw_uid)
        elif "win32" == sys.platform:
            pass

    def __exit__(self, type, value, traceback):
        if "darwin" == sys.platform:
            if self.noop is False:
                os.setegid(self.original_egid)
                os.seteuid(self.original_euid)
        elif "win32" == sys.platform:
            pass

        if isinstance(value, Exception):
            raise value

# lifted from: http://stackoverflow.com/questions/3812849/how-to-check-whether-a-directory-is-a-sub-directory-of-another-directory
def isSameDirOrChild(directory, test_child):
    directory = os.path.normpath(os.path.realpath(directory))
    test_child = os.path.normpath(os.path.realpath(test_child))
    if directory == test_child:
        return True

    # os.path.join, appending nothing adds a trailing seperator;
    # we want to avoid issues like, /a/b matching as the parent of
    # /a/bee/c
    directory = os.path.join(directory, '')

    # return true, if the common prefix of both is equal to directory
    # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    return os.path.commonprefix([test_child, directory]) == directory

def quietMakedirsInPreVeilDataDir(path):
    if isSameDirOrChild(preveilDataDir(), path) is False:
        raise Exception("path is not in data dir: %s" % path)

    with DoAsPreVeil() as _:
        if "darwin" == sys.platform:
            mask = os.umask(0o777)
            os.umask(mask)
            if (DATA_DIR_MODE & (~ mask)) != DATA_DIR_MODE:
                raise Exception("bad umask: %s" % mask)

        try:
            os.makedirs(path, DATA_DIR_MODE)
        except OSError:
            if not os.path.isdir(path):
                raise

def quietMkdirInPreVeilDataDir(path):
    if isSameDirOrChild(preveilDataDir(), path) is False:
        raise Exception("path is not in data dir: %s" % path)

    with DoAsPreVeil() as _:
        if "darwin" == sys.platform:
            mask = os.umask(0o777)
            os.umask(mask)
            if (DATA_DIR_MODE & (~ mask)) != DATA_DIR_MODE:
                raise Exception("bad umask: %s" % mask)

        try:
            os.mkdir(path, DATA_DIR_MODE)
        except OSError:
            if not os.path.isdir(path):
                raise

def file_no_ext(path):
    return os.path.splitext(os.path.basename(path))[0]

def preveilDataDir():
    if "darwin" == sys.platform:
        return os.path.join("/", "var", "preveil")
    elif "win32" == sys.platform:
        return os.path.join(os.getenv("SystemDrive") + "\\", "PreVeilData")
    elif "linux2" == sys.platform:
        return os.path.join("/", "var", "preveil")
    else:
        raise Exception("preveilDataDir: Unsupported platform")

def logsDir():
    return os.path.join(preveilDataDir(), "logs")

def tempDir():
    return os.path.join(preveilDataDir(), "temp")

def modesDir():
    return os.path.join(preveilDataDir(), "modes")

def getModeDir(mode):
    return os.path.join(modesDir(), mode)

# Handle cases where /var/preveil/* doesn't exist or it has the wrong
# owner:group
#
# This function tries to provide the following guarentee, if a process returns
# successfully from initDirs(), /var/preveil/* is available to it with the
# correct owner:group.  This guarentee is easier to provide if all processes
# only create these directories (or change their permissions) with this
# function.
def initDirs(mode):
    quietMkdirInPreVeilDataDir(preveilDataDir())
    quietMkdirInPreVeilDataDir(logsDir())
    quietMkdirInPreVeilDataDir(tempDir())
    quietMkdirInPreVeilDataDir(modesDir())
    quietMkdirInPreVeilDataDir(getModeDir(mode))

# Lifted from m000 @ http://stackoverflow.com/a/32888599
class CaseInsensitiveDict(dict):
    @classmethod
    def _k(cls, key):
        return key.lower() if isinstance(key, basestring) else key
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
        return super(CaseInsensitiveDict, self).has_key(self.__class__._k(key))
    def pop(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).pop(self.__class__._k(key), *args, **kwargs)
    def get(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).get(self.__class__._k(key), *args, **kwargs)
    def setdefault(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).setdefault(self.__class__._k(key), *args, **kwargs)
    def update(self, E={}, **F):
        super(CaseInsensitiveDict, self).update(self.__class__(E))
        super(CaseInsensitiveDict, self).update(self.__class__(**F))
    def _convert_keys(self):
        for k in list(self.keys()):
            v = super(CaseInsensitiveDict, self).pop(k)
            self.__setitem__(k, v)
