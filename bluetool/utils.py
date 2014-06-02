"""Utility functions
"""
import struct

_letohs8 = struct.Struct('<b')
_letoh16 = struct.Struct('<H')

def letohs8(buf, offset=0):
    return _letohs8.unpack_from(buf, offset)[0]

def letoh16(buf, offset=0):
    return _letoh16.unpack_from(buf, offset)[0]

def letoh24(buf, offset=0):
    val = _letoh16.unpack_from(buf, offset)[0]
    val |= (ord(buf[offset + 2]) << 16)
    return val;
