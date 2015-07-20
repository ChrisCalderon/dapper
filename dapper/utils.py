import os
import json
import sha3
from dapper.rpc_client import RPC_Client

################################################################################
#        1         2         3         4         5         6         7         8

def find_root():
    root = os.getcwd()
    while not (os.path.isdir(os.path.join(root, '.dapper')) or (root == '/')):
        root = os.path.dirname(root)
    assert root != '/', 'You are not in a dapper project!'
    return root

def get_db():
    root = find_root()
    return json.load(os.path.join(root, '.dapper', 'build.json'))

def save_db(db):
    root = find_root()
    json.dump(db, open(os.path.join(root, '.dapper', 'build.json'), 'w'))

def abi_int(x):
    return hex(x)[2:].rstrip('L').rjust(64, '0')

def abi_encode(args):
    data = ''
    array_data = ''
    len_args = 32*len(args) #in bytes
    for a in args:
        if type(a) == int:
            data += abi_int(a)
        if type(a) in (str, list):
            #d is byte offset of data from start
            d = len_args + len(array_data)/2
            data += abi_int(d)
            array_data += abi_int(len(a))
            this_data = ''
            while a:
                if type(a) == str:
                    this_data += hex(ord(a[0]))[2:]
                else:
                    this_data += abi_int(a[0])
                a = a[1:]
            len_data = len(this_data) #hex len
            len_mod64 = len_data%64
            if len_mod64:
                this_data = this_data.ljust(len_data + 64 - len_mod64, '0')
            array_data += this_data
    return data + array_data

def make_sig(args):
    sig = []
    for a in args:
        if type(a) == int:
            sig.append('int256')
        elif type(a) == str:
            sig.append('bytes')
        elif type(a) == list:
            sig.append('int256[]')
        else:
            raise ValueError('Bad argument type: {}; {}'.format(a, args))
    return ','.join(sig)

def abi_data(name, args):
    '''
    Name means the name of a function plus type info,
    as in the contract's full signature. Returns data
    suitable for sending in an RPC transaction.
    '''
    prefix = sha3.sha3_256(name).hexdigest()[:8]
    return '0x' + prefix + abi_encode(args)
