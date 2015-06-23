import dumbdbm
import os

def get_subdirs(path):
    '''Returns the list of subdirectories in this path.'''
    return set(os.walk(path).next()[1])

def get_build_paths(path):
    '''
    Returns paths that should exist if this is where
    the build database files are.'''
    datfile = 'build' + os.extsep + 'dat'
    dirfile = 'build' + os.extsep + 'dir'
    build_file1 = os.path.join(path, '.build', datfile)
    build_file2 = os.path.join(path, '.build', dirfile)
    return build_file1, build_file2

def has_build_db(path):
    '''Checks if the current path is the correct location for the build database.'''
    top_level_subdirs = [
        '.build',
        'src',
        'macros',
        'tests',
    ]
    subdirs = get_subdirs(path)
    is_top_level = all(subdir in subdirs for subdir in top_level_subdirs)
    return is_top_level and all(os.path.exists(p) for p in get_build_paths(path))

def is_not_root(path):
    '''Checks if the path is not the root path.'''
    return path != os.path.dirname(path)

def get_db(path=None):
    '''Finds and opens your dapper project's build db.'''
    if path = None:
        path = os.getcwd()
    assert is_not_root(path), 'You aren\'t in a dapped project!'
    if is_project_top_level(path):
        return dumbdbm.open(os.path.join(path, '.build', 'build'))
    else:
        return get_db(os.path.dirname(path))
