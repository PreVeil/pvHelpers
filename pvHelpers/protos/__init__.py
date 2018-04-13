from .keys_pb2 import UserKey, PublicUserKey, Key
from google.protobuf.message import Error, DecodeError, EncodeError
from google.protobuf.json_format import Error as JsonError, ParseError, SerializeToJsonError
from google.protobuf.descriptor import Error as DescError, TypeTransformationError

ProtobufErrors = (
    EncodeError, DecodeError, Error, \
    ParseError, SerializeToJsonError, \
    JsonError, TypeTransformationError, \
    DescError
)
