import os
from rpc_client import RPC_Client
from rpc_server import rpc_server
import dumbdbm

PATH = os.path.dirname(os.path.realpath(__file__))

def get_db():
    return dumbdbm.open(os.path.join(PATH, os.pardir, 'build'), 'c')
