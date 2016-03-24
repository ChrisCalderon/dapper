from .rpc_client_base import bytes_to_hex
from typing import List, Dict, Tuple, Any, Optional, Union
import re

# parses an ABI type into relevant info
ABI_TYPE = re.compile(
    "^(?P<base_type>u?fixed|u?int|bool|address|bytes|string)"
    "(?P<bits>(\d{1,3}x)?\d{1,3})?"
    "(?P<array>\[(?P<array_size>\d*)?\])?$")
# type expected from match_object.groupdict()
GroupDict = Dict[str,Optional[str]]
# python types with ABI equivalents
PythonAbiAnalog = Union[int,str,bytes,List[int],List[bytes]]

def encode_int(x: int, signed: bool) -> str:
    """Encodes x as an ABI int-like value. Use for encoding 'int',
    'uint', 'fixed', 'ufixed', 'bool', and 'address' types."""
    return bytes_to_hex(x.to_bytes(32, 'big', signed=signed))


def encode_bytes(x: bytes) -> str:
    """Encodes a static bytes<M> value."""
    return bytes_to_hex(x.ljust(32, b'\x00')[:32])


def encode_static_int_array(xs: List[int], signed: bool) -> str:
    """Encodes a static array of int-like values, e.g. 'int256[4]'."""
    return ''.join(encode_int(x, signed) for x in xs)


def encode_dynamic_int_array(xs: List[int], signed: bool) -> str:
    """Encodes a dynamic array of int-like values, e.g. 'int256[]'."""
    return encode_int(len(xs), False) + encode_static_array(xs, signed)


def encode_static_bytes_array(xs: List[bytes]) -> str:
    """Encodes a static array of the ABI type 'bytes<M>'."""
    return ''.join(map(encode_bytes, xs))


def encode_dynamic_bytes_array(xs: List[bytes]) -> str:
    """Encodes a dynamic array of the ABI type 'bytes<M>'."""
    return encode_int(len(xs), False) + encode_static_bytes_array(xs)


def encode_dynamic_bytes(x: bytes) -> str:
    """Encodes the ABI type 'bytes'."""
    padded_length = len(x) + 32 - len(x)%32
    padded_x = x.ljust(padded_length, b'\x00')
    return encode_int(len(x), False) + bytes_to_hex(padded_x)


def encode_string(x: str) -> str:
    """Encodes the ABI 'string' type."""
    return encode_dynamic_bytes(x.encode("utf8"))


signed_ints = {'int', 'fixed'}
ints = signed_ints.union({'uint', 'ufixed', 'bool', 'address'})


def int_check(match: GroupDict) -> Tuple[bool,bool]:
    return match['base_type'] in ints, match['base_type'] in signed_ints


def array_check(match: GroupDict) -> Tuple[bool,bool]:
    return match['array'] is not None, match['array_size'] is None


def bytes_check(match: GroupDict) -> bool:
    return match['base_type'] is 'bytes' and match['bits']


def encode(x: Any, abi_type: str) -> Tuple[str,str]:
    """Encodes 'x' as the ABI type 'abi_type', and flags whether
    or not 'x' was dynamic"""
    m = ABI_TYPE.match(abi_type)
    if m is None:
        raise ValueError("Bad ABI type: {}".format(abi_type))
    match = m.groupdict()
    is_int, is_signed = int_check(match)
    is_array, is_dynamic = array_check(match)
    is_bytes = bytes_check(match)
    if is_int and is_array and is_dynamic:
        return encode_dynamic_int_array(x, is_signed), "dynamic"
    elif is_int and is_array:
        return encode_static_int_array(x, is_signed), "static"
    elif is_int:
        return encode_int(x, is_signed), "static"
    elif is_bytes and is_array and is_dynamic:
        return encode_dynamic_bytes_array(x), "dynamic"
    elif is_bytes and is_array:
        return encode_static_bytes_array(x), "static"
    elif is_bytes:
        return encode_bytes(x), "static"
    elif match["base_type"] is "bytes":
        return encode_dynamic_bytes(x), "dynamic"
    elif match["base_type"] is "string":
        return encode_string(x), "dynamic"
    else:
        raise ValueError('Unexpected ABI type: {}'.format(abi_type))


def get_python_type(abi_type: str) -> type:
    """Gets the python type that corresponds with the given ABI type."""
    m = ABI_TYPE.match(abi_type)
    if m is None:
        raise ValueError("Bad ABI type: {}".format(abi_type))
    match = m.groupdict()
    is_int, _ = int_check(match)
    is_array, _ = array_check(match)
    is_bytes = bytes_check(match)
    if is_int and is_array:
        return List[int]
    elif is_int:
        return int
    elif is_bytes and is_array:
        return List[bytes]
    elif is_bytes:
        return bytes
    elif match['base_type'] is 'bytes':
        return bytes
    elif match['base_type'] is 'string':
        return str
    else:
        raise ValueError("Unexpected ABI type: {}".format(abi_type))


def encode_args(args: Tuple[PythonAbiAnalog], abi_types: Tuple[str]) -> str:
    """Encodes a tuple of python objects with the corresponding ABI types."""
    static_vals = []
    dynamic_vals = []
    dynamic_size = 0
    for arg, abi_type in zip(args, abi_types):
        encoded, kind = encode(arg, abi_type)
        if kind is "dynamic":
            static_vals.append(dynamic_size)
            dynamic_vals.append(encoded)
            dynamic_size += len(encoded)/2
        else:
            static_vals.append(encoded)
    for i, val in enumerate(static_vals):
        if isinstance(val, int):
            static_vals[i] = encode_int(val + 32*len(static_vals), False)
    return ''.join(static_vals) + ''.join(dynamic_vals)