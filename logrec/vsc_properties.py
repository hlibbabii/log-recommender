import logging
import os
import re

logger = logging.getLogger(__name__)

base_dir = os.environ['HOME']

current_script_location = os.path.realpath(__file__)
current_dir = os.path.dirname(current_script_location)
base_project_dir = os.path.dirname(current_dir)
logger.info(f'Base project dir is {base_project_dir}')

REWRITE_PARSED_FILE = False

with open(os.path.join(base_project_dir, 'VERSION'), 'r') as f:
    version = f.readline().rstrip('\n')
    major_version = re.fullmatch('([0-9]*)\..*', version).group(1)

DEFAULT_RAW_DATASETS_DIR = os.path.join(base_dir, 'raw_datasets', 'allamanis')
DEFAULT_PARSED_DATASETS_DIR = os.path.join(base_dir, 'prep_datasets', f'v{major_version}')

DEFAULT_DATASET = 'nodup_en_only'
DEFAULT_BPE_N_MERGES = '5000'
DEFAULT_BPE_BASE_REPR = '001001'

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
