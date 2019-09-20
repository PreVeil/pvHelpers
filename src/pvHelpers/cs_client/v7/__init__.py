from ..v6 import APIClientV6
from .test import TestV7


class APIClientV7(TestV7, APIClientV6):
    __api_version__ = u"v7"

    def __init__(self, backend):
        super(APIClientV7, self).__init__(backend)
