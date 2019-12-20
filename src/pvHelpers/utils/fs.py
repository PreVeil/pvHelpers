import os
import random
import sys
import time
import urllib
import urlparse

import yaml


if sys.platform in ["darwin", "linux2"]:
    import pwd


DATA_DIR_MODE = 0o750


def read_yaml_file(path):
    with open(path, u"r") as f:
        y = yaml.load(f.read())
    return y


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


def get_dir(path):
    return os.path.dirname(os.path.realpath(path))


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


def get_temp_file_path(mode_dir):
    return os.path.join(
        temp_dir(mode_dir),
        "%s.%s.%s" % (time.time(), random.randint(0, 1000000), os.getpid()))


# Handle cases where /var/preveil/* doesn't exist or it has the wrong
# owner:group
#
# This function tries to provide the following guarentee, if a process returns
# successfully from init_daemons_data_dirs(), /var/preveil/* is available to it with the
# correct owner:group.  This guarentee is easier to provide if all processes
# only create these directories (or change their permissions) with this
# function.
def init_daemons_data_dirs(wd, mode, is_test=False):
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
