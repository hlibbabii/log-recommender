import yaml

from logrec.properties import base_project_dir

__author__ = 'hlib'

import os
import sys

import logging
import logging.config

path = os.path.join(base_project_dir, 'logging.yaml')
if os.path.exists(path):
    with open(path, 'rt') as f:
        config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)
else:
    logging.basicConfig(level=logging.DEBUG)
logging.getLogger('matplotlib').setLevel(logging.INFO)

sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../fastai-fork'))