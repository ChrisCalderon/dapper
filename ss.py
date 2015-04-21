#!/usr/bin/python
from colorama import Style, Fore, init
from collections import defaultdict
from gethrpc import GethRPC
import leveldb
import serpent
import sys
import os
import re

def 

IMPORTP = re.compile(r'^import (?P<path>.*) as (?P<macro>)$', re.M)
ERROR = Style.BRIGHT + Fore.RED + 'ERROR!'
filedata = {}
dependencies = defaultdict(list)
paths = sys.argv[1:]
for path in paths:
    assert os.path.exists(path), ERROR + ' Path does not exist: %s' % path
    for top_dir, _, filenames in os.walk(path):
        for filename in filenames:
            filename = os.path.join(top_dir, filename)
            if filename.endswith('.se'):
                filedata[filename] = open(filename).read()
                for match in IMPORTP.finditer(filedata[filename]):
                    d = match.groupdict()
                    d['path'] = os.path.abspath(d['path'])
                    dependencies[d['path']].append((filename, d['macro']))


