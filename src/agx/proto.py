"""
Pure Python Protocol Buffers Varint Codec & Schema Serializer
============================================================
Handles encoding and decoding of Antigravity trajectory metadata blobs
without external binary or compiler dependencies.
"""

from typing import Any, List, Optional, Tuple


def decode_varint(data: bytes, pos: int) -> Tuple[int, int]:
    result = 0
    shift = 0
    data_len = len(data)
    while True:
        if pos >= data_len:
            raise ValueError(f"Truncated varint at position {pos}")
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
        if shift > 64:
            raise ValueError(f"Varint overflow at position {pos}")
    return result, pos


def encode_varint(value: int) -> bytes:
    data = bytearray()
    while value >= 0x80:
        data.append((value & 0x7F) | 0x80)
        value >>= 7
    data.append(value & 0x7F)
    return bytes(data)


def encode_string(field_num: int, val: str) -> bytes:
    val_bytes = val.encode("utf-8")
    tag = (field_num << 3) | 2
    return encode_varint(tag) + encode_varint(len(val_bytes)) + val_bytes


def parse_proto(data: bytes) -> List[Tuple[int, int, Any]]:
    pos = 0
    fields = []
    data_len = len(data)
    while pos < data_len:
        try:
            tag, pos = decode_varint(data, pos)
        except ValueError:
            break
        wire_type = tag & 7
        field_num = tag >> 3
        if wire_type == 0:
            try:
                val, pos = decode_varint(data, pos)
                fields.append((field_num, wire_type, val))
            except ValueError:
                break
        elif wire_type == 2:
            try:
                length, pos = decode_varint(data, pos)
            except ValueError:
                break
            if pos + length > data_len:
                break
            val = data[pos : pos + length]
            pos += length
            fields.append((field_num, wire_type, val))
        elif wire_type == 1:
            if pos + 8 > data_len:
                break
            val = data[pos : pos + 8]
            pos += 8
            fields.append((field_num, wire_type, val))
        elif wire_type == 5:
            if pos + 4 > data_len:
                break
            val = data[pos : pos + 4]
            pos += 4
            fields.append((field_num, wire_type, val))
        else:
            break
    return fields


def serialize_proto(fields: List[Tuple[int, int, Any]]) -> bytes:
    res = bytearray()
    for field_num, wire_type, val in fields:
        tag = (field_num << 3) | wire_type
        res += encode_varint(tag)
        if wire_type == 0:
            res += encode_varint(val)
        elif wire_type == 2:
            val_bytes = val if isinstance(val, (bytes, bytearray)) else str(val).encode("utf-8")
            res += encode_varint(len(val_bytes))
            res += val_bytes
        elif wire_type in (1, 5):
            res += val
    return bytes(res)


def make_timestamp(ts: float) -> bytes:
    sec = int(ts)
    nano = int((ts - sec) * 1e9)
    return encode_varint((1 << 3) | 0) + encode_varint(sec) + encode_varint((2 << 3) | 0) + encode_varint(nano)


def build_ide_info_proto(
    cid: str,
    title: str,
    step_count: int,
    workspace: str,
    mtime_epoch: float,
    existing_info: Optional[bytes] = None,
) -> bytes:
    """
    Constructs a complete, fully-compliant Protobuf record for the IDE trajectory summaries index.
    Includes Field 9 (Workspace URI), Field 17 (Context Metadata), Field 22 (Category Enum = 4).
    """
    ts_bytes = make_timestamp(mtime_epoch)
    f9 = encode_string(1, workspace) + encode_varint((3 << 3) | 2) + encode_varint(0)
    f17_parts = [
        encode_varint((1 << 3) | 2) + encode_varint(len(f9)) + f9,
        encode_varint((2 << 3) | 2) + encode_varint(len(ts_bytes)) + ts_bytes,
        encode_string(3, cid),
        encode_string(6, cid),
        encode_string(7, workspace),
    ]
    f17 = b"".join(f17_parts)

    if existing_info:
        fields = parse_proto(existing_info)
        updated_dict = {}
        for fn, wt, val in fields:
            if fn not in (1, 2, 7, 9, 10, 16, 17, 22):
                updated_dict[fn] = (wt, val)

        info_fields = [
            (1, 2, title.encode("utf-8")),
            (2, 0, step_count),
            (3, 2, updated_dict.get(3, (2, ts_bytes))[1]),
            (4, 2, updated_dict.get(4, (2, cid.encode("utf-8")))[1]),
            (5, 0, 1),
            (7, 2, ts_bytes),
            (9, 2, f9),
            (10, 2, ts_bytes),
            (15, 2, b""),
            (16, 0, step_count),
            (17, 2, f17),
            (22, 0, 4),
        ]
        return serialize_proto(info_fields)
    else:
        info_fields = [
            (1, 2, title.encode("utf-8")),
            (2, 0, step_count),
            (3, 2, ts_bytes),
            (4, 2, cid.encode("utf-8")),
            (5, 0, 1),
            (7, 2, ts_bytes),
            (9, 2, f9),
            (10, 2, ts_bytes),
            (15, 2, b""),
            (16, 0, step_count),
            (17, 2, f17),
            (22, 0, 4),
        ]
        return serialize_proto(info_fields)
