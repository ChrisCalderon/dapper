from .rpc_client_base import bytes_to_hex
from typing import List, re as Re, Set
import re

ABI_TYPE = re.compile(
    "^(?P<base_type>u?fixed|u?int|bool|address|bytes|string)"
    "(?P<bits>(\d{1,3}x)?\d{1,3})?"
    "(?P<array>\[(?P<array_size>\d*)?\])?$")

def encode_int(x: int, signed: bool) -> str:
    """Encodes x as an ABI int-like value. Use for encoding 'int',
    'uint', 'fixed', 'ufixed', 'bool', and 'address' types."""
    return bytes_to_hex(x.to_bytes(32, 'big', signed=signed))


def encode_bytes(x: bytes) -> str:
    """Encodes a static bytes<M> value."""
    return bytes_to_hex(x.ljust(32, b'\x00')[:32])


def encode_static_array(xs: List[int], signed: bool) -> str:
    """Encodes a static array of int-like values, e.g. 'int256[4]'."""
    return ''.join(encode_int(x, signed) for x in xs)


def encode_dynamic_array(xs: List[int], signed: bool) -> str:
    """Encodes a dynamic array of int-like values, e.g. 'int256[]'."""
    return encode_int(len(xs), False) + encode_static_array(xs, signed)


def encode_dynamic_bytes(x: bytes) -> str:
    """Encodes the ABI type 'bytes'."""
    padded_length = len(x) + 32 - len(x)%32
    padded_x = x.ljust(padded_length, b'\x00')
    return encode_int(len(x), False) + bytes_to_hex(padded_x)


def encode_string(x: str) -> str:
    """Encodes the ABI 'string' type."""
    return encode_dynamic_bytes(x.encode("utf8"))


def bit_check(match: Re.Match) -> bool:
    if match['bits'] is None:
        return False
    bits = int(match['bits'])
    return (8 <= bits <= 256) and (bits%8 == 0)


def check_int(match: Re.Match, types: Set[int]) -> bool:
    array_check = match['array'] is None
    return match['base_type'] in types and bit_check(match) and array_check


def is_signed_int(match: Re.Match) -> bool:
    return check_int(match, {'int', 'fixed'})


def is_unsigned_int(match):
    return check_int(match, {'uint', 'ufixed', 'bool', 'address'})


def is_dynamic_array(match):
    return match['array'] and match['array_size'] is None


def is_static_array(match):
    return match['array'] and match['array_size']


def is_dynamic_bytes(match):
    return match['base_type'] is 'bytes' and match['bits'] is None and \
           match['array'] is None


def is_string(match):
    return match['base_type'] is 'string' and match['bits'] is None and \
           match['array'] is None


def is_bytes(match):
    return match['base_type'] is 'bytes' and match['bits'] is None and \
           match['array'] is None


def encode(x: Any, abi_type: str) -> str:
    """Encodes 'x' as the ABI type 'abi_type'."""
    m = ABI_TYPE.match(abi_type)
    if m is None:
        raise ValueError("Bad ABI type: {}".format(abi_type))
    signed = m['base_type'] in ('int', 'fixed')
    if m['array'] and not m['array_size']:
        return encode_dynamic_array(x, signed)
    elif m['array'] and m['array_size']:
        return encode_static_array(x, signed)
    elif signed:
        return encode_int(x, signed)
    elif m['base_type']=='bytes' and m['bits']:
        return encode_bytes(x)
    elif m['base_type']=='bytes':
        return encode_dynamic_bytes()