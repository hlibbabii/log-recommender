import logging
import os


def attach_dataset_aware_handlers_to_loggers(name, main_log_name):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(os.path.join(name, main_log_name), 'w')
    formatter = logging.Formatter("%(levelname)s - %(asctime)s :%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
