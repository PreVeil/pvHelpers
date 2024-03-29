# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: keys.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='keys.proto',
  package='PVKeys',
  syntax='proto2',
  serialized_pb=_b('\n\nkeys.proto\x12\x06PVKeys\",\n\x03Key\x12\x18\n\x10protocol_version\x18\x01 \x01(\x04\x12\x0b\n\x03key\x18\x02 \x01(\x0c\"|\n\x07UserKey\x12\x18\n\x10protocol_version\x18\x01 \x01(\x04\x12\x13\n\x0bkey_version\x18\x02 \x01(\x04\x12 \n\x0bprivate_key\x18\x03 \x01(\x0b\x32\x0b.PVKeys.Key\x12 \n\x0bsigning_key\x18\x04 \x01(\x0b\x32\x0b.PVKeys.Key\"\x80\x01\n\rPublicUserKey\x12\x18\n\x10protocol_version\x18\x01 \x01(\x04\x12\x13\n\x0bkey_version\x18\x02 \x01(\x04\x12\x1f\n\npublic_key\x18\x03 \x01(\x0b\x32\x0b.PVKeys.Key\x12\x1f\n\nverify_key\x18\x04 \x01(\x0b\x32\x0b.PVKeys.Key\"I\n\nSealedData\x12\x18\n\x10protocol_version\x18\x01 \x01(\x04\x12\x12\n\nciphertext\x18\x02 \x01(\x0c\x12\r\n\x05proof\x18\x03 \x01(\x06')
)




_KEY = _descriptor.Descriptor(
  name='Key',
  full_name='PVKeys.Key',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='protocol_version', full_name='PVKeys.Key.protocol_version', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='key', full_name='PVKeys.Key.key', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=22,
  serialized_end=66,
)


_USERKEY = _descriptor.Descriptor(
  name='UserKey',
  full_name='PVKeys.UserKey',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='protocol_version', full_name='PVKeys.UserKey.protocol_version', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='key_version', full_name='PVKeys.UserKey.key_version', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='private_key', full_name='PVKeys.UserKey.private_key', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='signing_key', full_name='PVKeys.UserKey.signing_key', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=68,
  serialized_end=192,
)


_PUBLICUSERKEY = _descriptor.Descriptor(
  name='PublicUserKey',
  full_name='PVKeys.PublicUserKey',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='protocol_version', full_name='PVKeys.PublicUserKey.protocol_version', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='key_version', full_name='PVKeys.PublicUserKey.key_version', index=1,
      number=2, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='public_key', full_name='PVKeys.PublicUserKey.public_key', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='verify_key', full_name='PVKeys.PublicUserKey.verify_key', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=195,
  serialized_end=323,
)


_SEALEDDATA = _descriptor.Descriptor(
  name='SealedData',
  full_name='PVKeys.SealedData',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='protocol_version', full_name='PVKeys.SealedData.protocol_version', index=0,
      number=1, type=4, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='ciphertext', full_name='PVKeys.SealedData.ciphertext', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='proof', full_name='PVKeys.SealedData.proof', index=2,
      number=3, type=6, cpp_type=4, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=325,
  serialized_end=398,
)

_USERKEY.fields_by_name['private_key'].message_type = _KEY
_USERKEY.fields_by_name['signing_key'].message_type = _KEY
_PUBLICUSERKEY.fields_by_name['public_key'].message_type = _KEY
_PUBLICUSERKEY.fields_by_name['verify_key'].message_type = _KEY
DESCRIPTOR.message_types_by_name['Key'] = _KEY
DESCRIPTOR.message_types_by_name['UserKey'] = _USERKEY
DESCRIPTOR.message_types_by_name['PublicUserKey'] = _PUBLICUSERKEY
DESCRIPTOR.message_types_by_name['SealedData'] = _SEALEDDATA
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Key = _reflection.GeneratedProtocolMessageType('Key', (_message.Message,), dict(
  DESCRIPTOR = _KEY,
  __module__ = 'keys_pb2'
  # @@protoc_insertion_point(class_scope:PVKeys.Key)
  ))
_sym_db.RegisterMessage(Key)

UserKey = _reflection.GeneratedProtocolMessageType('UserKey', (_message.Message,), dict(
  DESCRIPTOR = _USERKEY,
  __module__ = 'keys_pb2'
  # @@protoc_insertion_point(class_scope:PVKeys.UserKey)
  ))
_sym_db.RegisterMessage(UserKey)

PublicUserKey = _reflection.GeneratedProtocolMessageType('PublicUserKey', (_message.Message,), dict(
  DESCRIPTOR = _PUBLICUSERKEY,
  __module__ = 'keys_pb2'
  # @@protoc_insertion_point(class_scope:PVKeys.PublicUserKey)
  ))
_sym_db.RegisterMessage(PublicUserKey)

SealedData = _reflection.GeneratedProtocolMessageType('SealedData', (_message.Message,), dict(
  DESCRIPTOR = _SEALEDDATA,
  __module__ = 'keys_pb2'
  # @@protoc_insertion_point(class_scope:PVKeys.SealedData)
  ))
_sym_db.RegisterMessage(SealedData)


# @@protoc_insertion_point(module_scope)
