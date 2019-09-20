import fipscrypto as FC
import libnacl

from pvHelpers.logger import g_log
from pvHelpers.protos import Key as KeyBuffer
from pvHelpers.protos import ProtobufErrors
from pvHelpers.protos import PublicUserKey as PublicUserKeyBuffer
from pvHelpers.protos import UserKey as UserKeyBuffer
from pvHelpers.utils import (b64dec, b64enc, jdumps, jloads, params,
                             utf8Decode, utf8Encode)

EC_SECRET_LENGTH  = FC.EC_PRIVATE_KEY_LENGTH
CURVE25519_PUB_KEY_LENGTH = FC.CURVE25519_PUB_KEY_LENGTH
NISTP256_PUB_KEY_LENGTH = FC.NISTP256_PUB_KEY_LENGTH

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
