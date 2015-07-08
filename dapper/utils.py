import os

def find_root():
    root = os.getcwd()
    while not (os.path.isdir(os.path.join(root, '.dapper')) or (root == '/')):
        root = os.path.dirname(root)
    assert root != '/', 'You are not in a dapper project!'
    return root

def get_db():
    root = find_root()
    return json.load(os.path.join(root, '.dapper', 'build.json'))

def save_db(db, update=False):
    root = find_root()
    if update:
        temp = get_db()
        temp.update(db)
        db = temp
    return json.dump(db, os.path.join(root, '.dapper', 'build.json'))
