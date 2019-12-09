import os
import random
import sys

import pytest

from pvHelpers.utils import (CaseInsensitiveDict, get_dir, parse_file_uri,
                             rand_unicode)


def randomize_casing(key):
    if isinstance(key, (str, unicode)):
        return "".join(map(lambda c: c.lower() if bool(random.getrandbits(1)) else c.upper(), list(key)))
    elif isinstance(key, tuple):
        return tuple([randomize_casing(i) for i in key])
    else:
        return key


def test_case_insensitive_dict():
    # test initialization
    k = rand_unicode()
    sensitive_dict = {
      1: rand_unicode(),
      k: rand_unicode(),
      randomize_casing(k): rand_unicode(),
      (1, rand_unicode(), rand_unicode()): rand_unicode()
    }
    insensitive_dict = CaseInsensitiveDict(sensitive_dict)
    assert len(sensitive_dict) == 4
    assert len(insensitive_dict) == 3

    # test addition
    for k in insensitive_dict.keys():
        for i in xrange(20):
            insensitive_dict[randomize_casing(k)] = rand_unicode()

        assert len(insensitive_dict) == 3

    # test access
    for k in insensitive_dict.keys():
        for i in xrange(20):
            assert insensitive_dict[k] == insensitive_dict[randomize_casing(k)]

    # deletion
    for k in insensitive_dict.keys():
        del insensitive_dict[randomize_casing(k)]

    assert len(insensitive_dict) == 0


def test_parse_file_uri_scheme():
    if sys.platform == "win32":
        p1 = "file://C:/test/doc.txt"
        required_download, uri = parse_file_uri(p1)
        assert not required_download
        assert uri == "C:\\test\\doc.txt"
        p2 = "file://C:/ProgramData/Cisco/Cisco AnyConnect Secure Mobility Client/aconnect.pac"
        required_download, uri = parse_file_uri(p2)
        assert not required_download
        assert uri == "C:\\ProgramData\\Cisco\\Cisco AnyConnect Secure Mobility Client\\aconnect.pac"

        p3 = "C:/ProgramData/Cisco/Cisco AnyConnect Secure Mobility Client/aconnect.pac"
        required_download, uri = parse_file_uri(p3)
        assert not required_download
        assert uri == "C:/ProgramData/Cisco/Cisco AnyConnect Secure Mobility Client/aconnect.pac"

        p4 = "file:///c:/path/to/the%20file.txt"
        required_download, uri = parse_file_uri(p4)
        assert not required_download
        assert uri == "C:\\path\\to\\the file.txt"

        for p in ["file:///pv/test/doc A.txt", "file:///pv/test/doc%20A.txt"]:
            required_download, uri = parse_file_uri(p)
            assert not required_download
            assert uri == "{}\\pv\\test\\doc A.txt".format(os.getenv("SystemDrive"))

        # TODO: how about a local network location?
        # e.g: file://hostname/path/to/the%20file.txt

    # no scheme
    valid_file = os.path.join(get_dir(__file__), "misc_test.py")
    required_download, uri = parse_file_uri(valid_file)
    assert not required_download
    assert uri == valid_file

    required_download, uri = parse_file_uri("file://" + valid_file)
    assert not required_download
    assert uri == valid_file

    # http and https
    for s in ["http", "https"]:
        u = "{}://pv.%7Etest%20hi.com".format(s)
        required_download, uri = parse_file_uri(u)
        assert required_download
        assert uri == u
