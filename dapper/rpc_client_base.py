"""Base class for json rpc clients."""
import os
import codecs
import ujson
from typing import Any, Union, List, Tuple, Dict, Optional, Callable

_hex = codecs.getencoder("hex")
JsonSafe = Union[int,
                 str,
                 List["JsonSafe"],
                 Tuple["JsonSafe", ...],
                 Dict[str, "JsonSafe"]]
JsonParams = Tuple[JsonSafe, ...]
JsonObject = Dict[str, JsonSafe]
JsonBatch = Union[Tuple[JsonObject, ...], List[JsonObject]]
ValidJsonMessage = Union[JsonObject, JsonBatch]


def bytes_to_hex(b: bytes) -> str:
    """Encodes a bytes object as a hex, unicode string."""
    return _hex(b)[0].decode("utf8")


class BaseRpcClient:
    def __init__(self, address: Any, verbose: bool):
        self.address = address
        self.verbose = verbose
        self.tag = "{}-{{}}".format(bytes_to_hex(os.urandom(8)))
        self.message_count = -1
        self.batch = []
        self.start_connection()

    def start_connection(self):
        """Starts the connection to the json rpc server."""
        raise NotImplemented()

    def close_connection(self):
        """Closes the connection to the json rpc server."""
        raise NotImplemented()

    def _send(self, message: bytes) -> bytes:
        """Sends json rpc to the server."""
        raise NotImplemented()

    def __send(self, json_stuff: ValidJsonMessage) -> ValidJsonMessage:
        """Encodes json objects, sends them, and prints if verbose is True."""
        json = ujson.encode(json_stuff)
        if self.verbose:
            print("Sending:", json)

        response = self._send(json.encode("utf8")).decode("utf8")
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
                 command: str,
                 *params: JsonParams,
                 batch: bool=False) -> Optional[JsonObject]:
        """Sends an rpc, or adds one to the current batch."""
        self.message_count += 1
        json = {"jsonrpc": "2.0",
                "id": self.tag.format(self.message_count),
                "method": command,
                "params": params}

        if batch:
            self.batch.append(json)
        else:
            return self.__send(json)

    def send_batch(self) -> Optional[JsonBatch]:
        """Sends the current rpc batch."""
        if self.batch:
            return self.__send(self.batch)

    def __getattr__(self, command: str) -> Callable[..., Optional[JsonObject]]:
        """Generates convenience functions for rpc."""
        def func(*params: JsonSafe, batch: bool=False) -> Optional[JsonObject]:
            return self.send_rpc(command, *params, batch=batch)
        func.__name__ = command
        func.__doc__ = '''\
Convenience function for the {} rpc.
    Setting `batch` to True adds to the current batch.'''.format(command)
        setattr(self, command, func)
        return func
