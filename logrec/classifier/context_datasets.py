import logging
import re

from torchtext import data

from logrec.util.io_utils import file_mapper

__author__ = 'hlib'

logger = logging.getLogger(__name__)

class ContextsDataset(data.Dataset):
    CONTEXTS_FILE_EXTENSION = "context.forward"
    LABEL_FILE_EXTENSION = "label"

    @staticmethod
    def sort_key(ex):
        return len(ex.text)

    @staticmethod
    def _get_pair(file_path):
        c_file_path = re.sub(f'{ContextsDataset.LABEL_FILE_EXTENSION}$',
                             f'{ContextsDataset.CONTEXTS_FILE_EXTENSION}',
                             file_path)
        return c_file_path, file_path


    def __init__(self, path, text_field, label_field, **kwargs):
        """Create an IMDB dataset instance given a path and fields.

        Arguments:
            path: Path to the dataset's highest level directory
            text_field: The field that will be used for text data.
            label_field: The field that will be used for label data.
            Remaining keyword arguments: Passed to the constructor of
                data.Dataset.
        """
        fields = [('text', text_field), ('label', label_field)]
        examples = []

        for c_filename, l_filename in file_mapper(path, ContextsDataset._get_pair, extension='label'):
            c_file = None
            l_file = None
            try:
                c_file = open(c_filename, 'r')
                l_file = open(l_filename, 'r')
                for context, level in zip(c_file, l_file):
                    example = data.Example.fromlist([context, (lambda l: l, level.rstrip('\n'))], fields)
                    examples.append(example)
            except FileNotFoundError:
                project_name = c_filename[:-len(ContextsDataset.CONTEXTS_FILE_EXTENSION)]
                logger.error(f"Project context not loaded: {project_name}")
                continue
            finally:
                if c_file is not None:
                    c_file.close()
                if l_file is not None:
                    l_file.close()

        if not examples:
            raise ValueError(f"Examples list is empty")

        super(ContextsDataset, self).__init__(examples, fields, **kwargs)

    @classmethod
    def splits(cls, text_field, label_field, path, train='train', test='test', **kwargs):
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
