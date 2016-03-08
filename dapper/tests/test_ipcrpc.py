import dapper.ipcrpc
import sys
import time

def main():
    client = dapper.ipcrpc.IPCRPC(verbose=True)
    client.eth_coinbase()
    for i in range(1000):
        client.eth_blockNumber()
        time.sleep(5)
    return 0

if __name__ == '__main__':
    sys.exit(main())
