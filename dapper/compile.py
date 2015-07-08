import warnings; warnings.simplefilter('ignore')
import serpent
from dapper.rpc_client import RPC_Client
import dapper.utils as u
from collections import defaultdict
import os
import sys
import json
import time

ROOT = u.find_root()
SOURCE = os.path.join(ROOT, 'src')
IMPORTS = True #import syntax is  better :^)
VERBOSITY = 0
BLOCKTIME = 12
FROM_DB = False
RPC = None
COINBASE = None
TRIES = 10
GAS = hex(3*10**6)
INFO = {}

def help():
    print '''\
Usage: dapper compile <command> [<option> ...]

Commands:
  help                           Shows this help message.
  all [<option> ...]             Compiles every file in src.
  <contract> [<option> ...]      Compiles the named contract.

Options:
  -b, --blocktime                The next argument is the blocktime to
                                 use, in seconds. Can be a float.
  -v, --verbosity                The next argument should be 1 to see
                                 the RPC messages, or 2 to see the HTTP
                                 as well as the RPC messages.
  -e, --externs                  By default, code is preprocessed to transform
                                 import syntax to native serpent externs.
                                 For example:
                                   import foo as FOO
                                 This gets translated into:
                                   extern foo.se:[bar:[int256]:int256]
                                   FOO = 0xdeadbeef
                                 This is much more convenient for new projects
                                 using more than one file, but it makes it
                                 harder to use with a large codebase that already
                                 uses externs. This option disables the
                                 preprocessing. Address variables need to have a
                                 a space around the equal sign, and need to be
                                 right beneath their corresponding extern line.
  -s, --source                   The next argument is the root dir of the
                                 code you wish to compile. It defaults
                                 to `<root>/src`, where root is the top
                                 directory of your project.
'''
################################################################################
#        1         2         3         4         5         6         7         8
def invalid_opts():
    print 'Invalid options!'
    help()
    sys.exit(1)

def read_options(opts):
    '''Reads user options and set's globals.'''
    global BLOCKTIME
    global VERBOSITY
    global IMPORTS
    global SOURCE
    
    i = 0
    while i < len(opts):
        if opts[i] in ('-b', '--bloctime'):
            if (i + 1) >= len(opts):
                invalid_opts()
            forbidden = map(float, (0, 'nan', '-inf', '+inf')) 
            b = float(opts[i+1])
            if b in forbidden:
                print 'Blocktime can not be 0, NaN, -inf, or +inf!'
                sys.exit(1)
            else:
                BLOCKTIME = b
            i += 2
        elif opts[i] in ('-v', '--verbosity'):
            if (i + 1) >= len(opts):
                invalid_opts()
            legal = (1, 2)
            v = int(opt[i+1])
            if v not in legal:
                print 'Verbosity must be 1 or 2!'
                sys.exit(1)
            else:
                VERBOSITY = v
            i += 2
        elif opts[i] in ('-i','-e', '--imports', '--exports'):
            if opts[i] in ('-i', '--imports'):
                
        elif opts(i) in ('-s', '--source'):
            if (i + 1) >= len(opts):
                invalid_opts()
            s = os.path.abspath(opts[i+1])
            if not(s.startswith(ROOT) and os.path.isdir(s)): 
                print 'Source path not a directoy or not in the project!'
                sys.exit(1)
            else:
                SOURCE = S
        
def get_fullname(name):
    '''
    Generates the fullname (path to the contract file) from a
    contract's short name (the file name minus extension, used
    in the import line.)
    '''
    for directory, subdirs, files in os.walk(SRCPATH):
        for f in files:
            if f[:-3] == name:
                return os.path.join(directory, f)
    raise ValueError('No such name: '+name)

def get_shortname(fullname):
    '''Extracts a shortname from a contract's fullname (it's path.)'''
    return os.path.split(fullname)[-1][:-3]

def wait(seconds):
    '''A shitty display while you wait! :^)'''
    sys.stdout.write('Waiting %f seconds' % seconds)
    sys.stdout.flush()
    for i in range(10):
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(seconds/10.)
    print

def broadcast_code(evm, address):
    '''Sends compiled code to the network, and returns the address.'''
    while True:
        response = RPC.eth_sendTransaction(sender=COINBASE, data=evm, gas=GAS)
        if 'result' in response:
            address = response['result']
            break
        else:
            assert 'error' in response and response['error']['code'] == -32603, \
                'Weird JSONRPC response: ' + str(response)
            if address is None:
                wait(BLOCKTIME)
            else:
                break
    tries = 0
    while tries < TRIES:
        wait(BLOCKTIME)
        check = RPC.eth_getCode(address)['result']
        if check != '0x' and check[2:] in evm:
            return address
        tries += 1
    return broadcast_code(evm, address)

def get_compile_order():
    # topological sorting! :3
    nodes = {}
    nodes_copy = {}
    avail = set()
    # for each node, build a list of it's incoming edges
    # incoming edges are dependencies
    for directory, subdirs, files in os.walk('src'):
        for f in files:
            incoming_edges = set() 
            for line in open(os.path.join(directory, f)):
                if USE_EXTERNS and line.startswith('extern'):
                    name = line[line.find(' ')+1:line.find(':')]
                    incoming_edges.add(name)
                if not USE_EXTERNS and line.startswith('import'):
                    name = line.split(' ')[1]
                    incoming_edges.add(name)
            nodes_copy[f[:-3]] = incoming_edges.copy()
            if incoming_edges:
                nodes[f[:-3]] = incoming_edges
            else:
                avail.add(f[:-3])
    
    sorted_nodes = []
    while avail:
        curr = avail.pop()
        sorted_nodes.append(curr)
        for item, edges in nodes.items():
            if curr in edges:
                edges.remove(curr)
            if not edges:
                avail.add(item)
                nodes.pop(item)
    return sorted_nodes, nodes_copy

def get_info(name):
    if FROM_DB:
        return json.loads(DB[name])
    else:
        return INFO[name]

def set_info(name, val):
    if FROM_DB:
        DB[name] = json.dumps(val)
    else:
        INFO[name] = val

def translate_code_with_imports(fullname):
    new_code = []
    for line in open(fullname):
        line = line.rstrip()
        if line.startswith('import'):
            line = line.split(' ')
            name, sub = line[1], line[3]
            info = get_info(name)
            new_code.append(info['sig'])
            new_code.append(sub + ' = ' + info['address'])
        else:
            new_code.append(line)
    return '\n'.join(new_code)

def translate_code_with_externs(fullname):
    new_code = []
    last_extern = float('+inf')
    for i, line in enumerate(open(fullname)):
        line = line.rstrip()
        if line.startswith('extern'):
            print line
            last_extern = i
            name = line[line.find(' ')+1:line.find(':')][:-3]
            info = get_info(name)
            new_code.append(info['sig'])
        elif i == last_extern + 1:
            sub = line.split(' ')[0]
            new_code.append(sub + ' = ' + info['address'])
        else:
            new_code.append(line)
    return '\n'.join(new_code)

def compile(fullname):
    if USE_EXTERNS:
        new_code = translate_code_with_externs(fullname)
    else:
        new_code = translate_code_with_imports(fullname)
#    print new_code
    evm = '0x' + serpent.compile(new_code).encode('hex')
    new_address = broadcast_code(evm)
    short_name = os.path.split(fullname)[-1][:-3]
    new_sig = serpent.mk_signature(new_code).replace('main', short_name, 1)
    fullsig = serpent.mk_full_signature(new_code)
    new_info = {'address':new_address, 'sig':new_sig, 'fullsig':fullsig}
    set_info(short_name, new_info)

def optimize_deps(deps, contract_nodes, contract):
    new_deps = [contract]
    for i in range(deps.index(contract) + 1, len(deps)):
        node = deps[i]
        for new_dep in new_deps:
            if new_dep in contract_nodes[node]:
                new_deps.append(node)
                break
    return new_deps

def main(args):
    read_options()
    deps, nodes = get_compile_order()
    if type(start) == str:
        deps = optimize_deps(deps, nodes, start)
        start = 0
    RPC = RPC_Client(default='GETH', verbose=verbose, debug=debug)
    COINBASE = RPC.eth_coinbase()['result']
    for i in range(start, len(deps)):
        fullname = get_fullname(deps[i])
        print "compiling", fullname
        compile(fullname)
    if not FROM_DB:
        sys.stdout.write('dumping new addresses to DB')
        sys.stdout.flush()
        for k, v in INFO.items():
            DB[k] = json.dumps(v)
            sys.stdout.write('.')
            sys.stdout.flush()
        print

