'''This module defines the RPCBase class, a base class for
JSON RPC client classes. See `RPCBase`'s documentation for
more info.'''

import ujson
import errno
import os
import socket
import codecs

__all__ = ['RPCBase']

_hex = codecs.getencoder('hex')


def hex(b):
    '''Encodes bytes as hex and returns a UTF8 string.'''
    return _hex(b)[0].decode('utf8')


def pprint(json_obj):
    print(ujson.dumps(json_obj, indent=2, sort_keys=True))


class RPCBase:
    '''A base class for socket based RPC Client implementations.

    This class defines some basic logic, functions, and members
    that need to be implemented by RPC clients.

    In particular, five members that are define by RPCBase class are
    self.message_id, self.tag, self.connection, self.batch, and
    self.verbose.

    self.message_id: an int the incremements for each message sent.
    self.tag: a random 10 character hex code, meant to help use
    the classes concurrently (with thread or processes.)
    self.batch: a list used to build up batches before sending.
    self.connection: a socket object which handles the connection.
    self.verbose: tells the client to pretty print json objects
    before they are sent and after they are recieved.

    There are two methods that need to be implemented by daughter
    classes: self.start_connection() and self.__send(json_bytes).

    self.start_connection(): no args. Sets up the connection socket.
    self.__send(json_bytes): accepts a single arg, json_bytes, and 
    sends it via whatever method (e.g. HTTP.) Must return the response
    json as a bytes object.
    '''
    def __init__(self, verbose=False):
        self.message_id = 0
        self.tag = hex(os.urandom(5)) + '-'
        self.batch = []
        self.verbose = verbose
        self.start_connection()
        

    def start_connection(self):
        '''Creates the socket connection needed for rpc.'''
        raise NotImplemented()


    def close_connection(self):
        '''Closes the rpc socket connection.'''
        self.connection.shutdown(socket.SHUT_RDWR)
        self.connection.close()


    def _send(self, json_bytes):
        '''Sends the json payload.'''
        raise NotImplemented()


    def __rpcify(self, command, params):
        '''Formats a pair of command name and params into jsonrpc.
        Side effect: increments self.message_id.'''
        result = { "jsonrpc":"2.0",
                   "method": command,
                   "params": params,
                   "id": self.tag + str(self.message_id)}
        self.message_id += 1
        return result


    @staticmethod
    def is_valid_json(json_bytes):
        try:
            ujson.decode(json_bytes.decode('utf8'))
        except ValueError:
            return False
        else:
            return True


    def __send_rpc(self, json_obj):
        if self.verbose:
            print('Sending:')
            pprint(json_obj)

        request_bytes = ujson.encode(json_obj).encode('utf8')
        result_bytes = self._send(request_bytes)
        result = ujson.decode(result_bytes.decode('utf8'))
        
        if self.verbose:
            print('Got:')
            pprint(result)
        return result
        

    def send_rpc(self, command, *params):
        return self.__send_rpc(self.__rpcify(command, params))


    def batch_rpc(self, commands):
        '''Sends several rpc commands at once.
        
        The commands argument should be a list of tuples like so:
        [
            ("command1", [*/ params list */]),
            ("command2", [/* more params*/]),
            ...
        ]
        '''
        return self.__send_rpc(list(map(self.__rpcify, *zip(*commands))))
 

    def add_to_batch(self, command, *params):
        '''Adds a command/params pair to the current batch.
        See the dpcumentation for self.batch_rpc'''
        self.batch.append((command, params))


    def send_batch(self):
        '''Sends the current batch.
        See the documentation for self.add_to_batch.'''
        self.batch_rpc(self.batch)
        self.batch = []
        

    def __getattr__(self, command):
        '''On-the-fly convenience functions for RPC.'''
        # easier interface for rpc
        # client.eth_coinbase() or
        # client.eth_coinbase(batch=True)
        #          vs        # client.send_rpc('eth_coinbase') or 
        # client.add_to_batch('eth_coinbase')
        func_code = '''\
def {0}(*params, batch=False):
    """Sends rpc command `{0}` with the given params.
    If batch is True, adds the command to the current batch,
    otherwise the command is sent immediately and returns a 
    json response."""
    if batch:
        self.add_to_batch('{0}', *params)
    else:
        return self.send_rpc('{0}', *params)

self.{0} = {0}'''.format(command)
        exec(func_code, {'self':self})
        return vars(self)[command]
