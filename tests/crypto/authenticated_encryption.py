import os
import random

from pvHelpers import AsymmBoxV3, PVKeyFactory

def test_get_shared_key():
  for _ in range(500):
    k = PVKeyFactory.newAsymmKey(3)
    k2 = PVKeyFactory.newAsymmKey(3)
    assert AsymmBoxV3.get_shared_key(k, k2.public_key) == AsymmBoxV3.get_shared_key(k2, k.public_key)

    plaintext = os.urandom(1024 * 20 + random.randint(0, 1024))
    cipher = AsymmBoxV3.encrypt(k, k2.public_key, plaintext)
    assert AsymmBoxV3.decrypt(k2, k.public_key, cipher) == plaintext
