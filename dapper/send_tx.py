import dapper.utils as u
from dapper.rpc_client import RPC_Client
import time

def main(args):
    if args[0] == 'help':
        print 'No help yet!'
        return

    assert len(args) >= 2, 'Not enough args: ' + str(args)
    contract = args[0]
    db = u.get_db()
    blocktime = 12
    assert contract in db, 'Unknown contract: ' + str(contract)
    for func_info in db[contract]['fullsig']:
        if func_info['name'].startswith(args[1]):
            name = func_info['name']
            break
    else:
        raise ValueError('Unknown function: ' + args[1])
    given_sig = u.make_sig(args[2:])
    sigerr = 'Bad arg types: <args: {}> <types: {}> <sig {}>'
    assert given_sig in name, sigerr.format(args[2:], given_sig, name)

    data = u.abi_data(name, args[2:])
    rpc = RPC_Client(default='GETH')
    txhash = rpc.eth_sendTransaction(to=db[contract]['address'], data=data)['result']
    while True:
        receipt = rpc.eth_getTransactionReceipt(txhash)
        if receipt['result'] is None:
            print 'No receipt available, trying again after %d seconds.'
            time.sleep(blocktime)
            continue
        break
