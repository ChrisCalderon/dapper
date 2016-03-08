'''This module defines an RPC client class that uses HTTP
for JSON RPC communication with the go-ethereum/alethzero clients.'''
import http.client
from rpc_client_base import RPCBase

__all__ = ['HTTPRPC']

REQUEST_HEADERS = {'User-Agent'   : 'dapper/1.0',
                   'Content-Type' : 'application/json',
                   'Accept'       : 'application/json'}

DEFAULT_ADDRESS = ('localhost', 8545)

class RPCClient(RPCBase):
    '''An RPC client class that for using JSON RPC over HTTP with 
    the go-ethereum and alethzero clients.'''
    def __init__(self, *, address=DEFAULT_ADDRESS, verbose=False):
        '''The `address` argument must be a tuple containing the
        address of the node you want to connect to. The default value
        for this is the default http rpc address for go-ethereum and
        alethzero.'''
        self.address = address
        super().__init__(verbose=verbose)

    def close_connection(self):
        '''Overrides the parent close_connection method since this
        class uses python's HTTPConnection.'''
        self.connection.close()

    def start_connection(self):
        '''Creates the HTTPConnection '''
        host = self.address[0]
        port = self.address[1]
        self.connection = http.client.HTTPConnection(host, port)

    def __send(self, json_bytes):
        '''Uses an HTTPConnection from the stdlib's http.client
        module to package json_bytes into an HTTP request.'''
        self.connection.request('POST', '/', json_bytes, 
                                REQUEST_HEADERS)

        response = self.connection.getresponse()
        return response.read()
