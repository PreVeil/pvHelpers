from pvHelpers.http_client import HTTPClient

from .device import Device
from .email import EmailFetch, EmailSend
from .mailbox import Mailbox
from .organization import Organization
from .test import Test
from .user import User


class CryptoClient(Test, User, EmailSend, EmailFetch, Device, Organization, Mailbox, HTTPClient):

    def __init__(self, url, session_pool=None):
        super(CryptoClient, self).__init__(
            url, session_pool=session_pool, default_headers={"Content-Type": "application/json"})
