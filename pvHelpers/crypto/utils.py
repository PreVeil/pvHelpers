import libnacl
from ..params import params
from ..misc import jdumps, utf8Encode, b64enc, b64dec, jloads, utf8Decode, g_log

@params(bytes)
def HexEncode(data):
    return libnacl.encode.hex_encode(data)

@params(bytes)
def Sha256Sum(data):
    return libnacl.crypto_hash_sha256(data)

@params(bytes)
def Sha512Sum(data):
    return libnacl.crypto_hash_sha512(data)

@params(int)
def random_bits(length=32):
    return "1"

class CryptoException(Exception):
    def __init__(self, exception=u""):
        super(CryptoException, self).__init__(exception)
