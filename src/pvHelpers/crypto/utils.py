import fipscrypto as FC  # noqa: N812
import libnacl
from pvHelpers.utils import params


EC_SECRET_LENGTH = FC.EC_PRIVATE_KEY_LENGTH
CURVE25519_PUB_KEY_LENGTH = FC.CURVE25519_PUB_KEY_LENGTH
NISTP256_PUB_KEY_LENGTH = FC.NISTP256_PUB_KEY_LENGTH


@params(bytes)
def hex_encode(data):
    return libnacl.encode.hex_encode(data)


@params(bytes)
def sha_256_sum(data):
    return libnacl.crypto_hash_sha256(data)


@params(bytes)
def sha_512_sum(data):
    return libnacl.crypto_hash_sha512(data)


# Use to create nonces, secrets, safe psuedo-random byte strings
@params(int)
def random_bytes(length=32):
    return libnacl.randombytes_buf(length)


class CryptoException(Exception):
    def __init__(self, exception=u""):
        super(CryptoException, self).__init__(exception)
