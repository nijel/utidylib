import sys
from epydoc.cli import cli

def run(argv=sys.argv):
    argv_old=sys.argv
    sys.argv=argv
    cli()
    sys.argv=argv_old

if __name__=='__main__':
    default='epydoc -o apidoc tidy/error.py tidy/lib.py tidy/__init__.py'.split()
    run(default)
