import libnacl
from ..params import params
from ..misc import jdumps, utf8Encode, b64enc, b64dec, jloads, utf8Decode, g_log
from ..protos import UserKey as UserKeyBuffer, PublicUserKey as PublicUserKeyBuffer, Key as KeyBuffer, ProtobufErrors

@params(bytes)
def HexEncode(data):
    return libnacl.encode.hex_encode(data)

@params(bytes)
def Sha256Sum(data):
    return libnacl.crypto_hash_sha256(data)

@params(bytes)
def Sha512Sum(data):
    return libnacl.crypto_hash_sha512(data)

# Use to create nonces, secrets, safe psuedo-random byte strings
@params(int)
def RandomBytes(length=32):
    return libnacl.randombytes_buf(length)

class CryptoException(Exception):
    def __init__(self, exception=u""):
        super(CryptoException, self).__init__(exception)
