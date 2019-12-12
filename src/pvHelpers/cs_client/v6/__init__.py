from ..v5 import APIClientV5
from .admin import PVAdminV6


class APIClientV6(PVAdminV6, APIClientV5):
    __api_version__ = 6
