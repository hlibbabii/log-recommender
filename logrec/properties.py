import os

if 'THESIS_DIR' in os.environ:
    from logrec.local_properties import *
else:
    from logrec.vsc_properties import *
