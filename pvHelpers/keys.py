import libnacl
import libnacl.public
import libnacl.sign
import libnacl.secret
import struct
from . import misc

# The first four bytes of encrypted data are reservered for internal use. When
# packing our bits with the struct module, make sure to pick a byte order (eg, >)
# otherwise python will choose native ordering and it might do something weird
# with alignment.
# The most sig bit of the first byte is the 'text' bit.
BINARY_BIT = 0x00
TEXT_BIT = 0x80
# The next three bits indicate encryption 'type'
ASYMM_BIT = 0x00
SEAL_BIT = 0x10
SECRET_BIT = 0x20

# "Raw" means we don't yet have the user_id
class RawPrivateKey:
    def __init__(self, version):
        self.__version = version
        self.__private_key = libnacl.public.SecretKey()
        self.__signing_key = libnacl.sign.Signer()

    def serializePublicKey(self):
        public_key = libnacl.public.PublicKey(self.__private_key.pk)
        verify_key = libnacl.sign.Verifier(self.__signing_key.hex_vk())
        return PublicKey.sSerialize(public_key, verify_key, self.__version)

    def convertToPrivateKey(self, user_id):
        return PrivateKey(user_id, self.__version, self.__private_key, self.__signing_key)

class AsymmBox:
    def __init__(self, private_key, public_key):
        self.__private_key = private_key
        self.__public_key = public_key
        self.__box = libnacl.public.Box(self.__private_key.getPrivateKey(), self.__public_key.getPublicKey())

    def encryptText(self, plaintext):
        if not isinstance(plaintext, unicode):
            return False, None

        status, bits = misc.utf8Encode(plaintext)
        if status == False:
            return False, None

        bits = struct.pack('>BBBB', TEXT_BIT | ASYMM_BIT, 0x00, 0x00, 0x00) + bits

        try:
            encrypted = self.__box.encrypt(bits)
        except (libnacl.CryptError, ValueError):
            return False, None

        return misc.b64enc(encrypted)

    def decryptText(self, ciphertext):
        if not isinstance(ciphertext, unicode):
            return False, None

        status, decoded_ciphertext = misc.b64dec(ciphertext)
        if status == False:
            return False, None

        try:
            bits = self.__box.decrypt(decoded_ciphertext)
        except (libnacl.CryptError, ValueError):
            return False, None

        header = struct.unpack('>BBBB', bits[:4])
        plaintext = bits[4:]

        if header[0] != (TEXT_BIT | ASYMM_BIT):
            return False, None

        return misc.utf8Decode(plaintext)

    def encryptBinary(self, plaintext):
        if not (isinstance(plaintext, bytes) or isinstance(plaintext, str)):
            return False, None

        bits = struct.pack('>BBBB', BINARY_BIT | ASYMM_BIT, 0x00, 0x00, 0x00) + plaintext

        try:
            encrypted = self.__box.encrypt(bits)
        except (libnacl.CryptError, ValueError):
            return False, None

        return misc.b64enc(encrypted)

    def decryptBinary(self, ciphertext):
        if not isinstance(ciphertext, unicode):
            return False, None

        status, decoded_ciphertext = misc.b64dec(ciphertext)
        if status == False:
            return False, None

        try:
            bits = self.__box.decrypt(decoded_ciphertext)
        except (libnacl.CryptError, ValueError):
            return False, None

        header = struct.unpack('>BBBB', bits[:4])
        plaintext = bits[4:]

        if header[0] != (BINARY_BIT | ASYMM_BIT):
            return False, None

        return True, plaintext

    def getPin(self):
        secret = self.__box._k
        status, secret_hash = sha512(secret)
        if status == False:
            return False, None
        return True, secret_hash[:8]

class PrivateKey:
    @staticmethod
    def deserialize(user_id, encoded_key):
        if not isinstance(user_id, unicode):
            return False, None
        if not isinstance(encoded_key, unicode):
            return False, None

        status, decoded = misc.b64dec(encoded_key)
        if status == False:
            return False, None
        status, decoded = misc.utf8Decode(decoded)
        if status == False:
            return False, None
        status, key = misc.jloads(decoded)
        if status == False:
            return False, None

        encoded_private_key = key.get("private_key")
        if encoded_private_key == None:
            msg = "missing 'private_key' field in encoded key"
            return False, None
        status, decoded = misc.b64dec(encoded_private_key)
        if status == False:
            msg = "invalid b64 for serialized private key"
            return False, None
        private_key = libnacl.public.SecretKey(decoded)

        encoded_signing_key = key.get("signing_key")
        if encoded_signing_key == None:
            msg = "missing 'signing_key' field in encoded key"
            return False, None
        status, decoded = misc.b64dec(encoded_signing_key)
        if status == False:
            msg = "invalid b64 for serialized signing key"
            return False, None
        signing_key = libnacl.sign.Signer(decoded)

        version = key.get("version")
        if version == None:
            msg = "missing 'version' field in encoded key"
            return False, None
        status, version = misc.toInt(version)
        if status == False:
            return False, None

        return True, PrivateKey(user_id, version, private_key, signing_key)

    @staticmethod
    def createAnonymousKey():
        raw_key = RawPrivateKey(-1)
        return raw_key.convertToPrivateKey(-1)

    def __init__(self, user_id, version, private_key, signing_key):
        self.__user_id = user_id
        self.__version = version
        self.__private_key = private_key
        self.__signing_key = signing_key

    def getPrivateKey(self):
        return self.__private_key

    def getSigningKey(self):
        return self.__signing_key

    def getVersion(self):
        return self.__version

    def getUser(self):
        return self.__user_id

    def serialize(self):
        status, encoded_private_key = misc.b64enc(self.__private_key.sk)
        if status == False:
            return False, None
        status, encoded_signing_key = misc.b64enc(self.__signing_key.seed)
        if status == False:
            return False, None
        status, version = misc.toInt(self.__version)
        if status == False:
            return False, None
        encoded = misc.jdumps({
            "private_key" : encoded_private_key,
            "signing_key" : encoded_signing_key,
            "version" : version,
        })
        status, encoded = misc.utf8Encode(encoded)
        if status == False:
            return False, None
        return misc.b64enc(encoded)

    def extractPublicKey(self):
        public_key = libnacl.public.PublicKey(self.__private_key.pk)
        verify_key = libnacl.sign.Verifier(self.__signing_key.hex_vk())
        return PublicKey(self.__user_id, self.__version, public_key, verify_key)

    def signText(self, data):
        if not isinstance(data, unicode):
            return False, None

        status, encoded = misc.utf8Encode(data)
        if status == False:
            return False, None

        return misc.b64enc(self.__signing_key.signature(encoded))

    def signBinary(self, data):
        if not isinstance(data, (str, bytes)):
            return False, None

        return misc.b64enc(self.__signing_key.signature(data))

    def unsealText(self, ciphertext):
        if not isinstance(ciphertext, unicode):
            return False, None

        status, ciphertext = misc.b64dec(ciphertext)
        if status == False:
            return False, None
        try:
            bits = self.__private_key.seal_open(ciphertext)
        except (libnacl.CryptError, ValueError) as e:
            return False, None

        header = struct.unpack('>BBBB', bits[:4])
        plaintext = bits[4:]

        if header[0] != (TEXT_BIT | SEAL_BIT):
            return False, None

        return misc.utf8Decode(plaintext)

    def unsealBinary(self, ciphertext):
        if not isinstance(ciphertext, unicode):
            return False, None

        status, ciphertext = misc.b64dec(ciphertext)
        if status == False:
            return False, None
        try:
            bits = self.__private_key.seal_open(ciphertext)
        except (libnacl.CryptError, ValueError) as e:
            return False, None

        header = struct.unpack('>BBBB', bits[:4])
        plaintext = bits[4:]

        if header[0] != (BINARY_BIT | SEAL_BIT):
            return False, None

        return True, plaintext

class PublicKey:
    @staticmethod
    def deserialize(user_id, string_key):
        if not isinstance(user_id, unicode):
            return False, None
        if not isinstance(string_key, unicode):
            return False, None

        status, key = misc.jloads(string_key)
        if status == False:
            return False, None

        public_key = key.get("public_key")
        if public_key == None:
            msg = "missing 'public_key' field in encoded key"
            return False, None
        status, public_key = misc.b64dec(public_key)
        if status == False:
            msg = "failed to b64 decode public key"
            return False, None
        public_key = libnacl.public.PublicKey(public_key)

        verify_key = key.get("verify_key")
        if verify_key == None:
            msg = "missing 'verify_key' field in encoded key"
            return False, None
        status, verify_key = misc.b64dec(verify_key)
        if status == False:
            msg = "failed to b64 decode verify key"
            return False, None
        verify_key = libnacl.sign.Verifier(libnacl.encode.hex_encode(verify_key))

        version = key.get("version")
        if version == None:
            msg = "missing 'version' field in encoded key"
            return False, None
        status, version = misc.toInt(version)
        if status == False:
            return False, None

        return True, PublicKey(user_id, version, public_key, verify_key)

    @staticmethod
    def sSerialize(public_key, verify_key, version):
        if not isinstance(public_key, libnacl.public.PublicKey):
            return False, None
        if not isinstance(verify_key, libnacl.sign.Verifier):
            return False, None
        if not isinstance(version, (int, long)):
            return False, None

        # The backend expects the components to be b64 encoded.
        status, encoded_public_key = misc.b64enc(public_key.pk)
        if status == False:
            return False, None
        status, encoded_verify_key = misc.b64enc(verify_key.vk)
        if status == False:
            return False, None
        return True, misc.jdumps({
            "public_key" : encoded_public_key,
            "verify_key" : encoded_verify_key,
            "version" : version,
        })

    def __init__(self, user_id, version, public_key, verify_key):
        self.__user_id = user_id
        self.__version = version
        self.__public_key = public_key
        self.__verify_key = verify_key

    def getVersion(self):
        return self.__version

    def getPublicKey(self):
        return self.__public_key

    def getVerifyKey(self):
        return self.__verify_key

    def serialize(self):
        return PublicKey.sSerialize(self.__public_key, self.__verify_key,
            self.__version)

    def verifyText(self, msg, sig):
        if not isinstance(msg, unicode):
            return False
        if not isinstance(sig, unicode):
            return False

        status, sig = misc.b64dec(sig)
        if status == False:
            return False

        status, encoded_msg = misc.utf8Encode(msg)
        if status == False:
            return False

        try:
            self.__verify_key.verify(sig + encoded_msg)
            return True
        except (libnacl.CryptError, ValueError) as e:
            return False

    def verifyBinary(self, msg, sig):
        if not isinstance(msg, (str, bytes)):
            return False
        if not isinstance(sig, unicode):
            return False

        status, sig = misc.b64dec(sig)
        if status == False:
            return False

        try:
            self.__verify_key.verify(sig + msg)
            return True
        except (libnacl.CryptError, ValueError) as e:
            return False

    def sealText(self, plaintext):
        if not isinstance(plaintext, unicode):
            return False, None

        status, bits = misc.utf8Encode(plaintext)
        if status == False:
            return False, None

        bits = struct.pack('>BBBB', TEXT_BIT | SEAL_BIT, 0x00, 0x00, 0x00) + bits

        try:
            sealed = self.getPublicKey().seal(bits)
        except (libnacl.CryptError, ValueError) as e:
            return False, None

        return misc.b64enc(sealed)

    def sealBinary(self, plaintext):
        if not (isinstance(plaintext, bytes) or isinstance(plaintext, str)):
            return False, None

        bits = struct.pack('>BBBB', BINARY_BIT | SEAL_BIT, 0x00, 0x00, 0x00) + plaintext

        try:
            sealed = self.getPublicKey().seal(bits)
        except (libnacl.CryptError, ValueError) as e:
            return False, None

        return misc.b64enc(sealed)

class SecretKey:
    @staticmethod
    def deserialize(encoded_key):
        if not isinstance(encoded_key, unicode):
            return False, None

        status, decoded = misc.b64dec(encoded_key)
        if status == False:
            return False, None
        status, decoded = misc.utf8Decode(decoded)
        if status == False:
            return False, None
        status, key = misc.jloads(decoded)
        if status == False:
            return False, None

        material = key.get("material")
        if material == None:
            return False, None
        status, material = misc.b64dec(material)
        if status == False:
            return False, None

        return True, SecretKey(material=material)

    def __init__(self, material=None):
        if material != None:
            self.__box = libnacl.secret.SecretBox(material)
        else:
            self.__box = libnacl.secret.SecretBox()

    def serialize(self):
        status, encoded_material = misc.b64enc(self.__box.sk)
        if status == False:
            return False, None
        encoded = misc.jdumps({u"material" : encoded_material})
        status, encoded = misc.utf8Encode(encoded)
        if status == False:
            return False, None
        return misc.b64enc(encoded)

    def encryptText(self, plaintext, details=None):
        if not isinstance(plaintext, unicode):
            return False, None
        if not (details == None or isinstance(details, dict)):
            return False, None

        status, bits = misc.utf8Encode(plaintext)
        if status == False:
            return False, None

        bits = struct.pack('>BBBB', TEXT_BIT | SECRET_BIT, 0x00, 0x00, 0x00) + bits

        try:
            ciphertext = self.__box.encrypt(bits)
        except (libnacl.CryptError, ValueError):
            return False, None

        if isinstance(details, dict):
            status, details['sha256'] = sha256(ciphertext)
            if status == False:
                return False, None
            details['length'] = len(ciphertext)
        return misc.b64enc(ciphertext)

    def decryptText(self, ciphertext):
        if not isinstance(ciphertext, unicode):
            return False, None

        status, ciphertext = misc.b64dec(ciphertext)
        if status == False:
            return False, None
        try:
            bits = self.__box.decrypt(ciphertext)
        except (libnacl.CryptError, ValueError) as e:
            return False, None

        header = struct.unpack('>BBBB', bits[:4])
        plaintext = bits[4:]

        if header[0] != (TEXT_BIT | SECRET_BIT):
            return False, None

        return misc.utf8Decode(plaintext)

    def encryptBinary(self, plaintext, details=None):
        if not (isinstance(plaintext, bytes) or isinstance(plaintext, str)):
            return False, None
        if not (details == None or isinstance(details, dict)):
            return False, None

        bits = struct.pack('>BBBB', BINARY_BIT | SECRET_BIT, 0x00, 0x00, 0x00) + plaintext

        try:
            ciphertext = self.__box.encrypt(bits)
        except (libnacl.CryptError, ValueError):
            return False, None

        if isinstance(details, dict):
            status, details['sha256'] = sha256(ciphertext)
            if status == False:
                return False, None
            details['length'] = len(ciphertext)
        return misc.b64enc(ciphertext)

    def decryptBinary(self, ciphertext):
        if not isinstance(ciphertext, unicode):
            return False, None

        status, ciphertext = misc.b64dec(ciphertext)
        if status == False:
            return False, None

        try:
            bits = self.__box.decrypt(ciphertext)
        except (libnacl.CryptError, ValueError) as e:
            return False, None

        header = struct.unpack('>BBBB', bits[:4])
        plaintext = bits[4:]

        if header[0] != (BINARY_BIT | SECRET_BIT):
            return False, None

        return True, plaintext

def sha256(data):
    if not (isinstance(data, bytes) or (isinstance, str)):
        return False, None
    return True, libnacl.encode.hex_encode(libnacl.crypto_hash_sha256(data))

def sha512(data):
    if not (isinstance(data, bytes) or (isinstance, str)):
        return False, None
    return True, libnacl.encode.hex_encode(libnacl.crypto_hash_sha512(data))
