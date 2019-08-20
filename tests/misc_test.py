import random

from pvHelpers import CaseInsensitiveDict, randUnicode


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