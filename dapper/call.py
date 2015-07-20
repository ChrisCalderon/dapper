import dapper.utils as u
from dapper.rpc_client import RPC_Client

# TODO - finish documentation for call, add more user options
def help():
    print '''\
Usage: dapper call <contract> <function> [<arg> ...]
'''

def main(args):
    if args[0] == 'help':
        print 'No help yet!'
        return

    assert len(args) >= 2, 'Not enough args: ' + str(args)
    contract = args[0]
    db = u.get_db()
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
    rpc.eth_call(to=db[contract]['address'], data=data)
