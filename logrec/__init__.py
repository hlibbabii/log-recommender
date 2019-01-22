__author__ = 'hlib'

import os
import sys

import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger('matplotlib').setLevel(logging.INFO)

sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '..'))
sys.path.insert(0, os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../fastai-fork'))