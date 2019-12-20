from pvHelpers.utils import b64enc, jdumps


def user_key_encrypt(self, plaintext, user_id, key_version):
    resp = self.put(
        u"{}/post/{}/encrypt".format(self.url, user_id),
        headers=self.__headers__,
        raw_body=jdumps({
            "encrypt_for": user_id,
            "plaintext": b64enc(plaintext)
        })
    )
    resp.raise_for_status()
    return resp.json()


def user_key_decrypt(self, ciphertext, user_id, key_version):
    resp = self.put(
        u"{}/post/{}/decrypt".format(self.url, user_id),
        headers=self.__headers__,
        raw_body=jdumps({
            "decrypt_key_version": key_version,
            "ciphertext": b64enc(ciphertext),
        })
    )
    resp.raise_for_status()
    return resp.json()


def user_key_sign(self, plaintext, user_id, key_version=None):
    resp = self.put(
        u"{}/post/{}/sign".format(self.url, user_id),
        headers=self.__headers__,
        raw_body=jdumps({
            "plaintext": b64enc(plaintext),
            "key_version": key_version
        })
    )
    resp.raise_for_status()
    return resp.json()


def user_key_verify(self, user_id, verify_for, key_version, plaintext, signature):
    resp = self.put(
        u"{}/post/{}/verify".format(self.url, user_id),
        headers=self.__headers__,
        raw_body=jdumps({
            "verify_from": verify_for,
            "key_version": key_version,
            "plaintext": b64enc(plaintext),
            "signature": b64enc(signature),
        })
    )
    resp.raise_for_status()
    return resp.json()
