from pvHelpers.utils import b64enc, jdumps


def user_encrypt(self, encrypt_for, plaintext, doas):
    resp = self.put(
        u"{}/post/{}/encrypt".format(self.url, doas),
        headers=self.__headers__,
        raw_body=jdumps({
            "encrypt_for": encrypt_for,
            "plaintext": b64enc(plaintext)
        })
    )
    resp.raise_for_status()
    return resp.json()


def user_decrypt(self, decrypt_for, decrypt_key_version, ciphertext):
    resp = self.put(
        u"{}/post/{}/decrypt".format(self.url, decrypt_for),
        headers=self.__headers__,
        raw_body=jdumps({
            "decrypt_key_version": decrypt_key_version,
            "ciphertext": b64enc(ciphertext),
        })
    )
    resp.raise_for_status()
    return resp.json()


def user_sign(self, signer_id, plaintext, key_version=None):
    resp = self.put(
        u"{}/post/{}/sign".format(self.url, signer_id),
        headers=self.__headers__,
        raw_body=jdumps({
            "plaintext": b64enc(plaintext),
            "key_version": key_version
        })
    )
    resp.raise_for_status()
    return resp.json()


def user_verify(self, verify_from, key_version, plaintext, signature, doas):
    resp = self.put(
        u"{}/post/{}/verify".format(self.url, doas),
        headers=self.__headers__,
        raw_body=jdumps({
            "verify_from": verify_from,
            "key_version": key_version,
            "plaintext": b64enc(plaintext),
            "signature": b64enc(signature),
        })
    )
    resp.raise_for_status()
    return resp.json()
