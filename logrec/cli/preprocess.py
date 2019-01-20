from logrec.dataprep.preprocess_params import pp_params
from logrec.dataprep.preprocessors import apply_preprocessors
from logrec.dataprep.preprocessors.general import from_string
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser
from logrec.dataprep.to_repr import init_splitting_config, to_repr
from logrec.properties import DEFAULT_DATASET, DEFAULT_BPE_BASE_REPR, DEFAULT_BPE_N_MERGES


def preprocess(s, r):
    parsed = apply_preprocessors(from_string(s), pp_params["preprocessors"], {
        'interesting_context_words': []
    })
    params = PrepParamsParser.from_encoded_string(r)
    init_splitting_config(DEFAULT_DATASET, params, DEFAULT_BPE_BASE_REPR, DEFAULT_BPE_N_MERGES, None)
    return to_repr(params, parsed)
