import importlib
import importlib.util
import logging
from functools import reduce
from types import ModuleType
from typing import Optional

__author__ = 'hlib'

logger = logging.getLogger(__name__)

def without_duplicates(list):
    seen = set()
    seen_add = seen.add
    return [x for x in list if not (x in seen or seen_add(x))]

def sum_vectors(vectors):
    if len(vectors) == 0:
        return [0.0, 0.0, 0.0, 0.0, 0.0]
    sum_vector = reduce(lambda x_vec, y_vec: [x + y for x,y in zip(x_vec, y_vec)], vectors)
    return [s / len(vectors) for s in sum_vector]


def get_params_module(params_path: Optional[str]) -> ModuleType:
    if params_path:
        logging.info(f'Loading params from {params_path}')
        spec = importlib.util.spec_from_file_location('logrec.param.templates', params_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        logger.info('Loading default params')
        module = importlib.import_module('logrec.param.templates')
    return module
