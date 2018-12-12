from enum import Enum, auto

from torchtext import data

from logrec.dataprep import base_project_dir


class Mode(Enum):
    TRAINING = auto()
    LEARNING_RATE_FINDING = auto()
    # ONLY_TESTING = auto()


params = {
    'path_to_classification_data': f'{base_project_dir}/nn-data/test/test1/classification/location/',
    'dataset_name': '104111',
    'base_model': '1_baseline',  # if there already exists a classifier with this name it is used, otherwise
    # lang model with this name is used
    'arch': {
        'bs': 64,
        'bptt': 150,
        'em_sz': 150,  # size of each embedding vector
        'nh': 300,     # number of hidden activations per layer
        'nl': 3,       # number of layers
        'min_freq': 0,
        'betas': [0.7, 0.99],
        'clip': 0.3,
        'reg_fn': {'alpha': 2, 'beta': 1},
        'drop': {'outi': 0.05, 'out': 0.05, 'w':0.1, 'oute': 0.02, 'outh': 0.05},
        'wds': 1e-6,
        'cycle': {'n': 1, 'len': 1, 'mult': 2},
        'training_metrics': ['accuracy', 'mrr']
    },
    'lr': 5.0 * 1e-3,
    'metrics': ['topk_1_10_100_cat_2', 'mrr'],
    'testing': {
        'how_many_words': 2000,
        'starting_words': "loading"
    },
    'mode': Mode.TRAINING
}

LEVEL_LABEL = data.Field(sequential=False)