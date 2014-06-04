"""Utility functions.
"""
import struct

_letohs8 = struct.Struct('<b')
_letoh16 = struct.Struct('<H')
_letoh32 = struct.Struct('<I')
_letoh64 = struct.Struct('<Q')

def htole8(val):
    return chr(val)

def htole16(val):
    return _letoh16.pack(val)

def htole24(val):
    return _letoh32.pack(val)[:3]

def htole32(val):
    return _letoh32.pack(val)

def htole64(val):
    return _letoh64.pack(val)

def letoh8(buf, offset=0):
    return ord(buf[offset])

def letohs8(buf, offset=0):
    return _letohs8.unpack_from(buf, offset)[0]

def letoh16(buf, offset=0):
    return _letoh16.unpack_from(buf, offset)[0]

def letoh24(buf, offset=0):
    val = _letoh16.unpack_from(buf, offset)[0]
    val |= (ord(buf[offset + 2]) << 16)
    return val;

def letoh32(buf, offset=0):
    return _letoh32.unpack_from(buf, offset)[0]

def letoh64(buf, offset=0):
    return _letoh64.unpack_from(buf, offset)[0]

