import os

if os.environ['HOME'] == '/home/hlib':
    print(f'$HOME is {os.environ["HOME"]}, using local_properties.py')
    from logrec.local_properties import *
elif os.environ['HOME'] == '/home/travis':
    print(f'$HOME is {os.environ["HOME"]}, using travis_properties.py')
    from logrec.travis_properties import *
else:
    print(f'$HOME is {os.environ["HOME"]}, using vsc_properties.py')
    from logrec.vsc_properties import *
