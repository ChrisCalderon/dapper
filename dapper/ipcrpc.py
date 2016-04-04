"""This module defines an RPC client class that uses an Unix domain
socket to communicate with the go-ethereum client."""
import socket
import os
import errno
from .rpc_client_base import BaseRpcClient

IpcAddress = str
default_address = os.path.join(os.path.expanduser('~'),
                               '.ethereum', 'geth.ipc')  # default path for go-ethereum
RECV_CHUNK = 4096 # max number of bytes to read from connection at a time.


class RpcClient(BaseRpcClient):
    """An RPC client class that uses go-ethereum's 'ipc' interface."""
    def __init__(self, *, address: IpcAddress=default_address, verbose: bool=False):
        super().__init__(verbose)
        self.connection = socket.socket(socket.AF_UNIX,
                                        socket.SOCK_STREAM)
        self.connection.connect(address)

    def close(self):
        """Closes the connection."""
        self.connection.shutdown(socket.SHUT_RDWR)
        self.connection.close()

    def _send(self, json: bytes) -> bytes:
        """Sends the json through the UDS connection to geth."""
        self.connection.sendall(json)
        result = bytearray()
        while not self.is_valid_json(result.decode("utf8")):
            result.extend(self.connection.recv(RECV_CHUNK))
        return bytes(result)
