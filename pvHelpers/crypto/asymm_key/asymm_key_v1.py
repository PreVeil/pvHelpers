from .asymm_key_base import *


class PublicKeyV1(PublicKeyBase):
    protocol_version = 1


class AsymmKeyV1(AsymmKeyBase):
    """
    AsymmKeyV0 just serialzied as protobuf
    """
    protocol_version = 1
