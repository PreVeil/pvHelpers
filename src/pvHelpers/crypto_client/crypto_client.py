from pvHelpers.http_client import HTTPClient

from .device import Device
from .email import EmailFetch, EmailSend
from .mailbox import Mailbox
from .organization import Organization
from .test import Test
from .user import User


class CryptoClient(Test, User, EmailSend, EmailFetch, Device, Organization, Mailbox, HTTPClient):
    __headers__ = {"Content-Type": "application/json"}

    def __init__(self, url):
        super(CryptoClient, self).__init__(url)
