import os
import dumbdbm

def main(name):
    dirs = [
        'src',
        'macros',
        '.build',
        'tests',
    ]
    os.mkdir(name)
    os.chdir(name)
    for d in dirs:
        os.mkdir(d)
    dumbdbm.open(os.path.join('.build', 'build'))
