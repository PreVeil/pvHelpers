import os

print os.environ.get('ENABLE_FIPS')
class USER_KEY_PROTOCOL_VERSION(object):
    V0 = 0
    V1 = 1

    Latest = 1

class ASYMM_KEY_PROTOCOL_VERSION(object):
    V0 = 0
    V1 = 1
    V2 = 2
    V3 = 3

    Latest = 3 if os.environ.get("ENABLE_FIPS", False) else 2

class SIGN_KEY_PROTOCOL_VERSION(object):
    V0 = 0
    V1 = 1
#   V2 = 2 skipped: https://github.com/PreVeil/core/wiki/Signing-Keys#protocol-version-2
    V3 = 3

    Latest = 3 if os.environ.get("ENABLE_FIPS", False) else 1

class SYMM_KEY_PROTOCOL_VERSION(object):
    V0 = 0
    V1 = 1

    Latest = 1 if os.environ.get("ENABLE_FIPS", False) else 0
