import pytest

from agx.proto import (
    build_ide_info_proto,
    decode_varint,
    encode_string,
    encode_varint,
    make_timestamp,
    parse_proto,
    serialize_proto,
)


def test_varint_codec():
    cases = [0, 1, 127, 128, 300, 16384, 2097151, 268435455, 4294967295]
    for val in cases:
        encoded = encode_varint(val)
        decoded, pos = decode_varint(encoded, 0)
        assert decoded == val
        assert pos == len(encoded)


def test_truncated_varint():
    # Byte with MSB set indicating more bytes, but stream ends
    truncated = bytes([0x80])
    with pytest.raises(ValueError, match="Truncated varint"):
        decode_varint(truncated, 0)


def test_encode_string():
    res = encode_string(1, "hello")
    # Tag for field 1, wire type 2 -> (1 << 3) | 2 = 10 (0x0A)
    assert res[0] == 10
    assert res[1] == 5  # len
    assert res[2:] == b"hello"


def test_proto_serialization_roundtrip():
    fields = [
        (1, 2, b"Session title"),
        (2, 0, 42),
        (3, 2, make_timestamp(1700000000.5)),
        (22, 0, 4),
    ]
    serialized = serialize_proto(fields)
    parsed = parse_proto(serialized)
    assert len(parsed) == 4
    assert parsed[0] == (1, 2, b"Session title")
    assert parsed[1] == (2, 0, 42)
    assert parsed[3] == (22, 0, 4)


def test_build_ide_info_proto():
    cid = "12345678-1234-5678-1234-567812345678"
    title = "Test Session Title"
    step_count = 10
    workspace = "file:///tmp/workspace"
    epoch = 1700000000.0

    proto_bytes = build_ide_info_proto(cid, title, step_count, workspace, epoch)
    parsed = parse_proto(proto_bytes)

    field_dict = {f[0]: f for f in parsed}
    # Check required fields
    assert 1 in field_dict  # Title
    assert field_dict[1][2].decode("utf-8") == title
    assert 2 in field_dict  # Step count
    assert field_dict[2][2] == step_count
    assert 9 in field_dict  # Workspace URI
    assert 17 in field_dict  # Context blob
    assert 22 in field_dict  # Category enum (4)
    assert field_dict[22][2] == 4
