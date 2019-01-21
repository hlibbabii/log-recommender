import os

base_dir = os.environ['HOME']
base_project_dir = os.path.join(base_dir, 'log-recommender')

REWRITE_PARSED_FILE = False

DEFAULT_RAW_DATASETS_DIR = os.path.join(base_dir, 'raw_datasets', 'devanbu', 'data')
DEFAULT_PARSED_DATASETS_DIR = os.path.join(base_project_dir, 'nn-data', 'new_framework')

DEFAULT_DATASET = 'en_100_percent'
DEFAULT_BPE_N_MERGES = '5000'
DEFAULT_BPE_BASE_REPR = '10111'

DEFAULT_PARSE_PROJECTS_ARGS = []
DEFAULT_PROJECT_LANGUAGE_CHECKER_ARGS = []
DEFAULT_TO_REPR_ARGS = []
DEFAULT_DATASET_GENERATOR_ARGS = []
DEFAULT_DATASET_STATS_ARGS = []
DEFAULT_VOCABSIZE_ARGS = []
DEFAULT_BPE_ARGS = []
DEFAULT_BPE_ENCODE_ARGS = []
DEFAULT_PREDICT_ARGS = []

DB_DBNAME = 'logrec'
DB_USER = 'logrec'
DB_HOST = '<host>'
DB_PASSWORD = '<password>'
