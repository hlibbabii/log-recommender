import logging

import torch

logger = logging.getLogger(__name__)


def print_gpu_info():
    available = gpu_available()
    logger.info(f'Using GPU: {str(available)}')
    if available:
        logger.info(f'Number of GPUs available: {get_n_gpus()}')
        logger.info(f'Using device: {get_current_device()}')


def get_n_gpus():
    return torch.cuda.device_count()


def gpu_available():
    return torch.cuda.is_available()


def get_current_device():
    return torch.cuda.current_device()
