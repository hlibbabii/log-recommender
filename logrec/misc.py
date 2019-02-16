import logging
import os


def attach_dataset_aware_handlers_to_loggers(name, main_log_name, logger_name=None):
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    logger.setLevel(level=logging.DEBUG)
    handler = logging.FileHandler(os.path.join(name, main_log_name), 'w')
    formatter = logging.Formatter("%(levelname)s - %(asctime)s :%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
