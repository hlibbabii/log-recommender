import os

base_dir = os.environ['THESIS_DIR'] if 'THESIS_DIR' in os.environ else os.environ['HOME']
base_project_dir = f'{base_dir}/log-recommender/'
