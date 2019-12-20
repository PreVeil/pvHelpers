from pvHelpers.user import LocalUser, LUserInfo, OrganizationInfo
from pvHelpers.utils import params

from .client import CryptoClient
from .remote_device import RemoteDevice
from .remote_user_key import RemoteUserKey


class RemoteUser(LocalUser):
    @params(object, CryptoClient, unicode, int, unicode, unicode,
            OrganizationInfo, LUserInfo, unicode, [RemoteUserKey], RemoteDevice)
    def __init__(self, crypto_client, user_id, account_version, display_name,
                 mail_cid, org_info, luser_info, password, user_keys, device):

        super(RemoteUser, self).__init__(
            user_id, account_version, display_name, mail_cid,
            org_info, luser_info, password, user_keys, device)

        self.crypto_client = crypto_client
