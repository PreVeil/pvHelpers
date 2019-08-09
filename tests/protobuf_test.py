
def test_protobuf_version():
    from google.protobuf.internal import api_implementation;
    assert api_implementation._implementation_type == "cpp"
