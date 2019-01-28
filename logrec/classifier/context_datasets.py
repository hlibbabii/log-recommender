import logging
import os
import random
import re

from torchtext import data

from logrec.dataprep import TRAIN_DIR, TEST_DIR
from logrec.dataprep.util import read_list
from logrec.infrastructure.fractions_manager import include_to_df
from logrec.util.files import file_mapper, get_dir_and_file

__author__ = 'hlib'

logger = logging.getLogger(__name__)

IGNORED_PROJECTS_FILE_NAME = "ignored_projects"


class ContextsDataset(data.Dataset):
    FW_CONTEXTS_FILE_EXT = "context.forward"
    BW_CONTEXTS_FILE_EXT = "context.backward"
    LABEL_FILE_EXT = "label"

    @staticmethod
    def sort_key(ex):
        return len(ex.text)

    @staticmethod
    def _get_pair(file_path):
        c_file_path_before = re.sub(f'{ContextsDataset.LABEL_FILE_EXT}$',
                             f'{ContextsDataset.FW_CONTEXTS_FILE_EXT}',
                                    file_path)
        c_file_path_after = re.sub(f'{ContextsDataset.LABEL_FILE_EXT}$',
                                   f'{ContextsDataset.BW_CONTEXTS_FILE_EXT}',
                                   file_path)
        return c_file_path_before, c_file_path_after, file_path

    @staticmethod
    def _prepare_context(context: str, context_len: int, reverse: bool = False) -> str:
        tokens = context.split(" ")
        if reverse:
            tokens.reverse()
        tokens = tokens[-context_len:]
        merged_tokens = " ".join(tokens)
        return merged_tokens

    @staticmethod
    def _get_context_for_prediction(context_before: str, context_after: str, context_len: int, backwards: bool):
        context = context_before if not backwards else context_after
        return ContextsDataset._prepare_context(context, context_len, reverse=backwards)

    def __init__(self, path, text_field, label_field, **kwargs):
        """Create an IMDB dataset instance given a path and fields.

        Arguments:
            path: Path to the dataset's highest level directory
            text_field: The field that will be used for text data.
            label_field: The field that will be used for label data.
            Remaining keyword arguments: Passed to the constructor of
                data.Dataset.
        """
        threshold = kwargs.pop("threshold", 0.0)
        context_len = kwargs.pop("context_len", 0)
        data_params = kwargs.pop("data", None)

        path_to_ignored_projects = os.path.join(path, '..', '..', '..', f"{IGNORED_PROJECTS_FILE_NAME}.{threshold}")
        logger.info(f"Loading ignored projects from {path_to_ignored_projects} ...")
        ignored_projects_set = set(read_list(path_to_ignored_projects))

        fields = [('text', text_field), ('label', label_field)]
        examples = []

        for c_filename_before, c_filename_after, l_filename in file_mapper(path, ContextsDataset._get_pair,
                                                                           extension='label'):
            if not include_to_df(os.path.basename(l_filename), data_params.percent, data_params.start_from):
                continue

            proj_name = re.sub(f"\.{ContextsDataset.LABEL_FILE_EXT}$", "", get_dir_and_file(l_filename))
            if proj_name in ignored_projects_set:
                continue

            c_file_before = None
            c_file_after = None
            l_file = None
            try:
                c_file_before = open(c_filename_before, 'r')
                c_file_after = open(c_filename_after, 'r')
                l_file = open(l_filename, 'r')
                for context_before, context_after, level in zip(c_file_before, c_file_after, l_file):
                    level = level.rstrip('\n')
                    if level:
                        context_for_prediction = ContextsDataset._get_context_for_prediction(context_before,
                                                                                             context_after,
                                                                                             context_len,
                                                                                             data_params.backwards)
                        example = data.Example.fromlist([context_for_prediction, level], fields)
                        examples.append(example)

            except FileNotFoundError:
                project_name = c_filename_before[:-len(ContextsDataset.FW_CONTEXTS_FILE_EXT)]
                logger.error(f"Project context not loaded: {project_name}")
                continue
            finally:
                if c_file_before is not None:
                    c_file_before.close()
                if c_file_after is not None:
                    c_file_after.close()
                if l_file is not None:
                    l_file.close()

        if not examples:
            raise ValueError(
                f"Examples list is empty. (percent={data_params.percent}, start from={data_params.start_from})")

        random.shuffle(examples)
        logger.debug(f"Number of examples gathered from {path}: {len(examples)} ")
        super(ContextsDataset, self).__init__(examples, fields, **kwargs)

    @classmethod
    def splits(cls, text_field, label_field, path, train=TRAIN_DIR, test=TEST_DIR, **kwargs):
        """Create dataset objects for splits of the IMDB dataset.

        Arguments:
            text_field: The field that will be used for the sentence.
            label_field: The field that will be used for label data.
            root: Root dataset storage directory. Default is '.data'.
            train: The directory that contains the training examples
            test: The directory that contains the test examples
            Remaining keyword arguments: Passed to the splits method of
                Dataset.
        """
        return super(ContextsDataset, cls).splits(
            path=path, text_field=text_field, label_field=label_field,
            train=train, validation=None, test=test, **kwargs)
