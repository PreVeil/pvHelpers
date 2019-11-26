import os


class USER_KEY_PROTOCOL_VERSION(object):  # noqa: N801
    V0 = 0
    V1 = 1

    Latest = 1


class ASYMM_KEY_PROTOCOL_VERSION(object):  # noqa: N801
    V0 = 0
    V1 = 1
    V2 = 2
    V3 = 3

    Latest = int(os.environ.get("ASYMM_KEY_PROTOCOL_VERSION", 3))


class SIGN_KEY_PROTOCOL_VERSION(object):  # noqa: N801
    V0 = 0
    V1 = 1
#   V2 = 2 skipped: https://github.com/PreVeil/core/wiki/Signing-Keys#protocol-version-2
    V3 = 3

    Latest = int(os.environ.get("SIGN_KEY_PROTOCOL_VERSION", 3))


class SYMM_KEY_PROTOCOL_VERSION(object):  # noqa: N801
    V0 = 0
    V1 = 1

    Latest = int(os.environ.get("SYMM_KEY_PROTOCOL_VERSION", 1))
