import os

base_dir = os.environ['THESIS_DIR'] if 'THESIS_DIR' in os.environ else os.environ['HOME']
base_project_dir = f'{base_dir}/log-recommender/'

path_to_dicts = f"{base_project_dir}/dicts/"
path_to_non_eng_dicts = f"{path_to_dicts}/non-eng"
path_to_eng_dicts = f'{path_to_dicts}/eng'

TRAIN_DIR = 'train'
TEST_DIR = 'test'
VALID_DIR = 'valid'

METADATA_DIR = 'metadata'
REPR_DIR = 'repr'
CLASSIFICATION_DIR = 'classification'

TEXT_FIELD_FILE = 'TEXT.pkl'

MODELS_DIR = 'models'
