'''This module defines an RPC client class that uses an Unix domain
socket to communicate with the go-ethereum client.'''

import socket
import errno
import os
from .rpc_client_base import RPCBase

__all__ = ['IPCRPC']

# TODO: write installer to insulate geth install in
# it's own user/group, and update this to default to
# that ipc path.

# TODO: find out if alethzero has ipc capabilities...
IPC_PATH = os.path.join(os.path.expanduser('~'),
                        '.ethereum',
                        'geth.ipc')
RECV_CHUNK = 4096 # max number of bytes to read from connection at a time.

class RPCClient(RPCBase):
    '''An RPC client class that uses go-ethereum's 'ipc' interface.'''
    def __init__(self, *, ipc_path=IPC_PATH, verbose=False):
        '''The ipc_path variable defaults to the standard ipc path
        for go ethereum, but you may pass in a different path if
        you've configured your go-ethereum daemon differently.'''
        self.ipc_path = ipc_path
        super().__init__(verbose=verbose)

    def start_connection(self):
        '''Creates the UDS socket and connects to the given ipc socket path.'''
        self.connection = socket.socket(socket.AF_UNIX,
                                        socket.SOCK_STREAM)
        self.connection.connect(self.ipc_path)
        self.connection.settimeout(0)

    def _send(self, json_bytes):
        '''Sends the json bytes through the UDS connection to geth.'''

        self.connection.sendall(json_bytes)
        response = bytearray()
        timeout = 0
        eps = 0.001
        while not self.is_valid_json(response):
            try:
                chunk = self.connection.recv(RECV_CHUNK)
            except socket.timeout:
                timeout = 2*timeout + eps
                self.connection.settimeout(timeout)
            else:
                response.extend(chunk)

        return response
