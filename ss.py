#!/usr/bin/python
import warnings; warnings.simplefilter('ignore')
from colorama import Style, Fore, init
from collections import defaultdict
from gethrpc import GethRPC
import leveldb
import serpent
import json
import sys
import os
import re

DB = leveldb.LevelDB('/.build')
IMPORTP = re.compile(r'^import (?P<path>.*) as (?P<macro>.*)$', re.M)
ERROR = Style.BRIGHT + Fore.RED + 'ERROR!'

def depth(filename, count=0):
    return max((count if filename not in dependencies[f] else depth(f, count+1)) for f in dependencies)

def default():
    return {'date':0.0, 'sig':'', 'fullsig':'', 'address':''}

def load(filename):
    try:
        return json.loads(db.Get(filename))
    except:
        return default()

def macro(address, name):
    return 'macro %(name)s:\n    %(address)s\n'%locals()

def main():
    filedata = {}
    dependencies = defaultdict(list)
    imports = defaultdict(list)
    paths = sys.argv[1:]
    for path in paths:
        assert os.path.exists(path), ERROR + ' Path does not exist: %s' % path
        os.chdir(path)
        

    fileinfo = {}
    for d, filename in sorted(zip(map(depth, dependencies), dependencies)):
        info = load(filename)
        date = os.path.getmtime(filename)
        if info['date'] < date:
            info['date'] = date
            info['sig'] = serpent.mk_signature(filename)
            info['fullsig'] = serpent.mk_full_signature(filename)
            for m, d in imports[filename]:
                a = fileinfo[d['path']]['address']
                s = fileinfo[d['path']]['sig']
                import_line = m.string[m.start():m.end()]
                replacement = s + '\n' + macro(a, d['macro'])
                filedata[filename].replace(
