import http.client
from .rpc_client_base import BaseRpcClient
from typing import Tuple

REQUEST_HEADERS = {'User-Agent': 'dapper/1.0',
                   'Content-Type': 'application/json',
                   'Accept': 'application/json'}
default_address = ('localhost', 8545)
AddressType = Tuple[str, int]


class RpcClient(BaseRpcClient):
    def __init__(self, *,
                 address: AddressType=default_address,
                 verbose: bool=False):
        super().__init__(address, verbose)

    def start_connection(self):
        host = self.address[0]
        port = self.address[1]
        self.connection = http.client.HTTPConnection(host, port)

    def close_connection(self):
        self.connection.close()

    def _send(self, json: bytes) -> bytes:
        self.connection.request('POST', '/', json,
                                REQUEST_HEADERS)

        response = self.connection.getresponse()
        return response.read()
