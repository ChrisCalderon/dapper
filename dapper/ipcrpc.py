"""This module defines an RPC client class that uses an Unix domain
socket to communicate with the go-ethereum client."""
import socket
import os
import errno
from .rpc_client_base import BaseRpcClient

AddressType = str
default_address = os.path.join(os.path.expanduser('~'),
                               '.ethereum', 'geth.ipc')
RECV_CHUNK = 4096 # max number of bytes to read from connection at a time.


class RpcClient(BaseRpcClient):
    """An RPC client class that uses go-ethereum's 'ipc' interface."""
    def __init__(self, *, address: str=default_address, verbose: bool=False):
        super().__init__(address, verbose)

    def start_connection(self):
        """Creates the UDS socket and connects to the given ipc socket path."""
        self.connection = socket.socket(socket.AF_UNIX,
                                        socket.SOCK_STREAM)
        self.connection.connect(self.address)
        self.connection.settimeout(0)

    def close_connection(self):
        """Closes the connection."""
        self.connection.shutdown(socket.SHUT_RDWR)
        self.connection.close()

    def _send(self, json: bytes) -> bytes:
        """Sends the json through the UDS connection to geth."""
        self.connection.sendall(json)
        response = bytearray()
        timeout = 0
        eps = 0.001
        while not self.is_valid_json(response):
            try:
                chunk = self.connection.recv(RECV_CHUNK)
            except socket.timeout:
                timeout = 2*timeout + eps
                self.connection.settimeout(timeout)
            except socket.error as exc:
                if exc.errno != errno.EAGAIN:
                    raise
            else:
                response.extend(chunk)
        self.connection.settimeout(0)

        return bytes(response)
