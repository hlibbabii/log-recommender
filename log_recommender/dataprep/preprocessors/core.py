import importlib
import logging
import time
from functools import partial


preps_to_required_params_dict = {
    'same_case_split.split': ['splitting_file_path'],
    'java.strip_off_identifiers': ['interesting_context_words'],
    'repr.to_repr': ['verbosity_params']
}

def names_to_functions(pp_names, context):
    pps = []
    for name in pp_names:
        file_name, func_name = name[0:name.rindex(".")], name[name.rindex(".")+1:]
        file = importlib.import_module('dataprep.preprocessors.' + file_name)
        func = getattr(file, func_name)
        if name in preps_to_required_params_dict:
            pps.append(partial(func, *list(map(lambda x: context[x], preps_to_required_params_dict[name]))))
        else:
            pps.append(func)
    return pps


def apply_preprocessors(to_be_processed, preprocessors, context={}):
    if not preprocessors:
        return to_be_processed
    if isinstance(next(iter(preprocessors)), str):
        preprocessors = names_to_functions(preprocessors, context)
    for preprocessor in preprocessors:
        start = time.time()
        to_be_processed = preprocessor(to_be_processed)
        t = int(time.time() - start)
        if t > 0:
            logging.debug(f"{preprocessor}: {t}s")
    return to_be_processed