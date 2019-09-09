import random

from pvHelpers import CaseInsensitiveDict, randUnicode, parse_file_uri


def randomize_casing(key):
    if isinstance(key, (str, unicode)):
        return "".join(map(lambda c: c.lower() if bool(random.getrandbits(1)) else c.upper(), list(key)))
    elif isinstance(key, tuple):
        return tuple([randomize_casing(i) for i in key])
    else:
        return key


def test_case_insensitive_dict():
    # test initialization
    k = randUnicode()
    sensitive_dict = {
      1: randUnicode(),
      k: randUnicode(),
      randomize_casing(k): randUnicode(),
      (1, randUnicode(), randUnicode()): randUnicode()
    }
    insensitive_dict = CaseInsensitiveDict(sensitive_dict)
    assert len(sensitive_dict) == 4
    assert len(insensitive_dict) == 3

    # test addition
    for k in insensitive_dict.keys():
        for i in xrange(20):
            insensitive_dict[randomize_casing(k)] = randUnicode()

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
    p1 = "file://C:/test/doc.txt"
    assert parse_file_uri(p1) == "C:/test/doc.txt"
    p2 = "file://C:/ProgramData/Cisco/Cisco AnyConnect Secure Mobility Client/aconnect.pac"
    assert parse_file_uri(
        p2
    ) == "C:/ProgramData/Cisco/Cisco AnyConnect Secure Mobility Client/aconnect.pac"

    p3 = "C:/ProgramData/Cisco/Cisco AnyConnect Secure Mobility Client/aconnect.pac"
    assert parse_file_uri(
        p3
    ) == "C:/ProgramData/Cisco/Cisco AnyConnect Secure Mobility Client/aconnect.pac"
