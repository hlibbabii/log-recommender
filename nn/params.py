from torchtext import data

nn_params = {
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
}

TEXT = data.Field()
LEVEL_LABEL = data.Field(sequential=False)