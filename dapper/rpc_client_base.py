"""Base class for json rpc clients."""
import os
import codecs
import ujson
from typing import Any, Union, List, Tuple, Dict, Optional, Callable

_hex = codecs.getencoder("hex")
JsonObject = Dict[str, Union[int, str, List['JsonObject'], 'JsonObject']]
JsonParams = Tuple[JsonObject, int, str]
JsonBatch = List[JsonObject]
JsonMessage = Union[JsonObject, JsonBatch]


def bytes_to_hex(b: bytes) -> str:
    """Encodes a bytes object as a hex, unicode string."""
    return _hex(b)[0].decode("utf8")


class BaseRpcClient:
    def __init__(self, verbose: bool):
        self.verbose = verbose
        self.tag = "{}-{{}}".format(bytes_to_hex(os.urandom(8)))
        self.message_count = -1
        self.batch = []

    def _send(self, message: bytes) -> bytes:
        """Sends json rpc to the server."""
        raise NotImplemented()

    def send_json_message(self, json: JsonMessage) -> JsonMessage:
        """Sends a json message and returns the result."""
        encoded_json = ujson.encode(json)
        if self.verbose:
            print("Sending:", encoded_json)

        response = self._send(encoded_json.encode("utf8")).decode("utf8")
        if self.verbose:
            print("Got:", response)

        return ujson.decode(response)

    @staticmethod
    def is_valid_json(json: str) -> bool:
        try:
            ujson.decode(json)
        except:
            return False
        else:
            return True

    def send_rpc(self,
                 method: str,
                 *params: JsonParams,
                 batch: bool=False) -> Optional[JsonObject]:
        """Creates a json message with the given method and params,
        then sends it or adds it to the current batch."""
        self.message_count += 1
        json = {"jsonrpc": "2.0",
                "id": self.tag.format(self.message_count),
                "method": method,
                "params": params}

        if batch:
            self.batch.append(json)
        else:
            return self.send_json_message(json)

    def send_batch(self) -> Optional[JsonBatch]:
        """Sends the current rpc batch."""
        if self.batch:
            return self.send_json_message(self.batch)

    def __getattr__(self, method: str) -> Callable[..., Optional[JsonObject]]:
        """Generates convenience functions for rpc."""
        def func(*params: JsonParams, batch: bool=False) -> Optional[JsonObject]:
            return self.send_rpc(method, *params, batch=batch)
        func.__name__ = method
        func.__doc__ = '''\
Convenience function for the '{}' rpc.
    Setting `batch` to True adds to the current batch.'''.format(method)
        setattr(self, method, func)
        return func
