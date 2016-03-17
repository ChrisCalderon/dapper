import dapper.ipcrpc
import sys
import time

def main():
    client = dapper.ipcrpc.RPCClient(verbose=True)
    client.eth_coinbase()
    client.send_rpc('eth_getBlockByNumber', 815859, False)
    
    for i in range(10):
        client.eth_getBlockByNumber(i, False, batch=True)
    client.send_batch()

if __name__ == '__main__':
    sys.exit(main())
