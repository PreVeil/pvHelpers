from pvHelpers.api_client import APIClient

from .device import Device
from .email import EmailFetch, EmailSend
from .mailbox import Mailbox
from .organization import Organization
from .user import User
from .test import Test

class CryptoClient(Test, User, EmailSend, EmailFetch, Device, Organization, Mailbox, APIClient):
    __headers__ = {"Content-Type": "application/json"}

    def __init__(self, url):
        super(CryptoClient, self).__init__(url)
