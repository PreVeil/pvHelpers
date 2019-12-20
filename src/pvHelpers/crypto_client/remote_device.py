from pvHelpers.crypto_client import CryptoClient
from pvHelpers.user import CURRENT_PLATFORM, LocalDevice
from pvHelpers.utils import params

from .remote_user_key import RemoteUserKey


class RemoteDevice(LocalDevice):
    @params(object, CryptoClient, unicode, unicode, dict, unicode)
    def __init__(self, client, id_, name, metadata, status):
        # NOTEXX
        super(RemoteDevice, self).__init__(
            id_, name, RemoteUserKey(), metadata, status, CURRENT_PLATFORM)
