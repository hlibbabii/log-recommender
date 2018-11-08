import importlib
import logging
import time

logger = logging.getLogger(__name__)

def names_to_functions(pp_names):
    pps = []
    for name in pp_names:
        file_name, func_name = name[0:name.rindex(".")], name[name.rindex(".")+1:]
        file = importlib.import_module('logrec.dataprep.preprocessors.' + file_name)
        func = getattr(file, func_name)
        pps.append(func)
    return pps


def apply_preprocessors(to_be_processed, preprocessors, context={}):
    if not preprocessors:
        return to_be_processed
    if isinstance(next(iter(preprocessors)), str):
        preprocessors = names_to_functions(preprocessors)
    for preprocessor in preprocessors:
        start = time.time()
        preprocessor_output = preprocessor(to_be_processed, context)
        if isinstance(preprocessor_output, tuple):
            to_be_processed, add_to_context = preprocessor_output
            for (k,v) in add_to_context:
                context[k] = v
        else:
            to_be_processed = preprocessor_output
        t = int(time.time() - start)
        if t > 0:
            logger.debug(f"{preprocessor}: {t}s")
    return to_be_processed