from .. import httprpc
import sys
import traceback


def main() -> int:
    exit_code = 0
    try:
        client = httprpc.RpcClient(verbose=True)
        client.eth_coinbase()
        client.send_rpc('eth_getBlockByNumber', 815859, False)

        for i in range(10):
            client.eth_getBlockByNumber(i, False, batch=True)
        client.send_batch()
    except:
        traceback.print_exc()
        exit_code = 1
    finally:
        return exit_code

if __name__ == '__main__':
    sys.exit(main())