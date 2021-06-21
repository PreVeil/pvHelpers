import os
import random
import pytest

from pvHelpers import AsymmBoxV3, PVKeyFactory

@pytest.mark.parametrize("use_fips_derivation", [True, False])
def test_get_shared_key(use_fips_derivation):
  for _ in range(500):
    k = PVKeyFactory.newAsymmKey(3)
    k2 = PVKeyFactory.newAsymmKey(3)
    assert AsymmBoxV3.get_shared_key(k, k2.public_key, use_fips_derivation) == AsymmBoxV3.get_shared_key(k2, k.public_key, use_fips_derivation)

    plaintext = os.urandom(1024 * 20 + random.randint(0, 1024))
    cipher = AsymmBoxV3.encrypt(k, k2.public_key, plaintext, use_fips_derivation)
    assert AsymmBoxV3.decrypt(k2, k.public_key, cipher, use_fips_derivation) == plaintext
