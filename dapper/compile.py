import warnings; warnings.simplefilter('ignore')
import math
import serpent
from dapper.rpc_client import RPC_Client
import dapper.utils as u
from collections import defaultdict
import os
import sys
import json
import time

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
                                 harder to use with a large codebase that
                                 already uses externs. This option disables the
                                 preprocessing. Address variables need to have
                                 a space around the equal sign, and need to be
                                 right beneath their corresponding extern line.
  -s, --source                   The next argument is the root dir of the
                                 code you wish to compile. It defaults
                                 to `<root>/src`, where root is the top
                                 directory of your project.
'''

################################################################################
#        1         2         3         4         5         6         7         8

ROOT = None
SOURCE = None
IMPORTS = True #import syntax is  better :^)
VERBOSITY = 0
BLOCKTIME = 12
DB = None
RPC = None
COINBASE = None
TRIES = 10
GAS = hex(int(math.pi*1e6))

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
    SOURCE = os.path.join(u.find_root(), 'src')
    i = 0
    bad_floats = map(float, (0, 'nan', '-inf', '+inf'))
    verb_vals = 1, 2
    while i < len(opts):
        if opts[i] in ('-b', '--blocktime'):
            if (i + 1) >= len(opts):
                invalid_opts()
            try:
                b = float(opts[i+1])
            except ValueError as exc:
                print "Error:", exc
                sys.exit(1)
            if b in bad_floats:
                print 'Blocktime can not be 0, NaN, -inf, or +inf!'
                sys.exit(1)
            else:
                BLOCKTIME = b
            i += 2
        elif opts[i] in ('-v', '--verbosity'):
            if (i + 1) >= len(opts):
                invalid_opts()
            try:
                v = int(opt[i+1])
            except ValueError as exc:
                print "Error:", exc
                sys.exit(1)
            if v not in verb_vals:
                print 'Verbosity must be 1 or 2!'
                sys.exit(1)
            else:
                VERBOSITY = v
            i += 2
        elif opts[i] in ('-e', '--exports'):
            IMPORTS = False
        elif opts(i) in ('-s', '--source'):
            if (i + 1) >= len(opts):
                invalid_opts()
            s = os.path.abspath(opts[i+1])
            if not(s.startswith(ROOT) and os.path.isdir(s)): 
                print 'Source path not a directoy or not in the project!'
                sys.exit(1)
            else:
                SOURCE = s
        
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

def broadcast_code(evm):
    '''Sends compiled code to the network, and returns the address.'''
    receipt_hash = RPC.eth_sendTransaction(
        sender=COINBASE,
        data=evm,
        gas=GAS)['result']
    wait(BLOCKTIME)
    receipt = RPC.eth_getTransactionReceipt(receipt_hash)
    address = receipt['contractAddress']
    code = RPC.eth_getCode(address)['result']
    assert code[2:] in evm, "dat code is fucked!"
    return address

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
                if not IMPORTS and line.startswith('extern'):
                    name = line[line.find(' ')+1:line.find(':')]
                    incoming_edges.add(name)
                if IMPORTS and line.startswith('import'):
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

def translate_code_with_imports(fullname):
    new_code = []
    for line in open(fullname):
        line = line.rstrip()
        if line.startswith('import'):
            line = line.split(' ')
            name, sub = line[1], line[3]
            info = DB[name]
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
            last_extern = i
            name = line[line.find(' ')+1:line.find(':')][:-3]
            info = DB[name]
            new_code.append(info['sig'])
        elif i == last_extern + 1:
            sub = line.split(' ')[0]
            new_code.append(sub + ' = ' + info['address'])
        else:
            new_code.append(line)
    return '\n'.join(new_code)

def compile(fullname):
    if IMPORTS:
        new_code = translate_code_with_imports(fullname)
    else:
        new_code = translate_code_with_externs(fullname)
    evm = '0x' + serpent.compile(new_code).encode('hex')
    new_address = broadcast_code(evm)
    short_name = os.path.split(fullname)[-1][:-3]
    new_sig = serpent.mk_signature(new_code).replace('main', short_name, 1)
    fullsig = json.loads(serpent.mk_full_signature(new_code))
    new_info = {'address':new_address, 'sig':new_sig, 'fullsig':fullsig}
    DB[short_name] = new_info

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
    u.save_db(db)
