from enum import Enum, auto

from torchtext import data


class Mode(Enum):
    TRAINING = auto()
    LEARNING_RATE_FINDING = auto()
    ONLY_TESTING = auto()


nn_params = {
    'arch': {
        'path_to_data': '../nn-data',
        'model_name': 'few_data',
        # 'model_name': 'devanbu_no_replaced_identifier_split',
        'bs': 32,
        'bptt': 70,
        'em_sz': 300,  # size of each embedding vector
        'nh': 400,     # number of hidden activations per layer
        'nl': 3,       # number of layers
        'min_freq': 5,
        'betas': [0.7, 0.99],
        'clip': 0.3,
        'reg_fn': {'alpha': 2, 'beta': 1},
        'drop': {'outi': 0.05, 'out': 0.05, 'w':0.1, 'oute': 0.02, 'outh': 0.05},
        'lr': 1e-3, 'wds': 1e-6,
        'cycle': {'n': 1, 'len': 1, 'mult': 2},
        'training_metrics': ['accuracy', 'f2', 'mrr_non_interactive']
    },
    'metrics': ['topk_1_10_100_cat_2', 'mrr'],
    'testing': {
        'how_many_words': 1000,
        'starting_words': "public <identifier> ( ) throws"
    },
    'mode': Mode.TRAINING
}

LEVEL_LABEL = data.Field(sequential=False)