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
HEADER_LENGTH = 4
