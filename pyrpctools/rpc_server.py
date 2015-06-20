'''
A JSON RPC server for simulating an ethereum node for tests.
'''
import json
from types import *
from time import strftime, gmtime, time
from http import simple_server
from ethereum import tester, transactions

GAS_LIMIT = 3141592
STATE = tester.state()
GAS_PRICE = 1
# Everything's always OK :^)
RESPONSE = '''\
HTTP/1.1 200 OK\r
Date: %(date)s\r
Content-Type: application/json\r
Content-Length: %(length)d\r
\r
%(body)s'''

def get_time():
    return strftime('%a, %d %b %Y %T GMT', gmtime()) 

INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
PARSE_ERROR = -32700
ERRORS = {
    INVALID_REQUEST:'Invalid Request',
    METHOD_NOT_FOUND:'Method not found',
    INVALID_PARAMS:'Invalid params',
    INTERNAL_ERROR:'Internal error',
    PARSE_ERROR:'Parse error',
}

def make_rpc_obj(type, data, id):
    return {'jsonrpc':'2.0', type:data, 'id':id}

def make_result(result, id):
    return make_rpc_obj('result', result, id)

def make_error(error_code, id=None):
    return make_rpc_obj('error', {'code':error_code, 'message':ERRORS[error_code]}, id)

def make_response(rpc_obj):
    body = json.dumps(rpc_obj)
    return RESPONSE % {'date':get_time(), 'length':len(body), 'body':body}

def is_bad_rpc(rpc_obj):
    if type(rpc_obj) != DictType:
        return True
    required_fields = {
        'jsonrpc':lambda v: v==u'2.0', 
        'id':lambda v: type(v) in (IntType, LongType, UnicodeType, FloatType, NoneType),
        'method':lambda v: type(v) is UnicodeType and all(ord(c) < 128 for c in v),
        }
    for field, pred in required_fields.items():
        if field not in rpc_obj:
            return True
        if not pred(rpc_obj[field]):
            return True
    return False

def call(rpc_request):
    method = rpc_request['method']
    if method.startswith('eth_'):
        try:
            func = globals()[method]
        except:
            return make_error(METHOD_NOT_FOUND)
        try:
            result = func(*rpc_request.get('params', []))
        except TypeError, ValueError:
            return make_error(INVALID_PARAMS, rpc_request['id'])
        except:
            return make_error(INTERNAL_ERROR, rpc_request['id']) 
        else:
            return make_result(result, rpc_request['id'])
    return make_error(METHOD_NOT_FOUND, rpc_request['id'])

def handler(http_request):
    try:
        rpc_request = json.loads(http_request['body'])
    except:
        return make_response(make_error(PARSE_ERROR))
    result = ''
    if type(rpc_request) == list:
        result = []
        for req in rpc_request:
            if is_bad_rpc(req):
                result.append(make_error(INVALID_REQUEST))
            else:
                result.append(call(req))
        result = filter(None, result)
    else:
        if is_bad_rpc(rpc_request):
            result = make_error(INVALID_REQUEST)
        else:
            result = call(rpc_request)
    if result:
        return make_response(result)
    else:
        return ''

def rpc_server(addr, port):
    simple_server(addr, port, handler)

def mine_on_fail(thunk):
    try:
        return thunk()
    except:
        STATE.mine()
    return thunk()

def eth_coinbase():
    return '0x' + STATE.block.coinbase.encode('hex')
    
def eth_getBalance(address):
    return STATE.block.account_to_dict(address[:2].decode('hex'))['balance']

def eth_blocknumber():
    return hex(STATE.block.number).rstrip('L')

def eth_accounts():
    return ["0x" + a.encode('hex') for a in tester.accounts]

def eth_gasPrice():
    return hex(GAS_PRICE).rstrip('L')

def eth_sendTransaction(tx):
    addr = tx.get('from', tester.accounts[0].encode('hex')).lstrip('0x').decode('hex')
    key = tester.keys[tester.accounts.index(addr)]
    value = tx.get('value', 0)
    to = tx.get('to', '').lstrip('0x').decode('hex')
    data = tx.get('data', '').lstrip('0x').decode('hex')
    gas = tx.get('gas', '').lstrip('0x')

    send_nonce = STATE.block.get_nonce(addr)
    tx = tester.t.Transaction(send_nonce, GAS_PRICE, GAS_LIMIT, to, value, data)
    STATE.last_tx = tx
    tx.sign(key)
    s, o = tester.pb.apply_transaction(STATE.block, tx)
    STATE.mine(1)
    return '0x' + o.encode('hex')

def eth_getCode(contract_address):
    return '0x' + STATE.block.get_code(contract_address.lstrip('0x').decode('hex')).encode('hex')

def eth_getTransactionByHash(txhash):
    txhash = txhash.lstrip('0x').decode('hex').rjust(32, '\x00')
    for blocknumber, block in enumerate(STATE.blocks):
        for txindex, tx in block.get_transactions():
            if tx.hash == txhash:
                break
        else:
            continue
        break
    else:
        return None
    return {
        'hash': '0x' + txhash.encode('hex'),
        'nonce': hex(tx.nonce).rstrip('L'),
        'blockHash': '0x' + block.hash.encode('hex'),
        'blockNumber': hex(blocknumber).rstrip('L'),
        'transactionIndex': hex(txindex).rstrip('L'),
        'from': '0x' + tx.sender.encode('hex'),
        'to': '0x' + tx.to.encode('hex'),
        'value': hex(tx.value).rstrip('L'),
        'gas': hex(tx.startgas).rstrip('L'),
        'gasPrice': hex(tx.gasPrice).rstrip('L'),
        'input': '0x' + tx.data.encode('hex'),
    }
