import logging
import os
import shutil
from typing import Optional

import dill as pickle
from shutil import copyfile

from torchtext.data import Field

from fastai.nlp import RNN_Learner
from logrec.dataprep import MODELS_DIR, TEXT_FIELD_FILE, REPR_DIR, TRAIN_DIR, VALID_DIR, TEST_DIR
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser
from logrec.infrastructure.config_manager import find_most_similar_config, find_name_for_new_config
from logrec.infrastructure.fractions_manager import normalize_percent_data
from logrec.local_properties import DEFAULT_PARSED_DATASETS_DIR
from logrec.param.model import Data, Arch
from logrec.util import io_utils

logger = logging.getLogger(__name__)

CLASSIFICATION_DIR_NAME = "classification"


class FS(object):
    def __init__(self, dataset: str, repr: str, base_model: str, classification_type: Optional[str] = None):
        self._dataset = dataset
        self._repr = repr
        self._base_model = base_model
        self._classification_type = classification_type
        self._model_name = None

        if self._classification_type:
            self._create_and_get_path_to_classifier()

    @property
    def dataset(self):
        return self._dataset

    @property
    def repr(self):
        return self._repr

    @property
    def base_model(self):
        return self._base_model

    #################################################333

    @property
    def path_to_lang_model_dataset(self):
        return os.path.join(DEFAULT_PARSED_DATASETS_DIR, self._dataset, REPR_DIR, self._repr)

    @property
    def path_to_classification_dataset(self):
        if not self._classification_type:
            raise ValueError("Classification type is not set! "
                             "Are you running a langmodel? "
                             "Did you forget to specify classification_type param when creating FS?")
        if not self._base_model:
            raise AssertionError('Base model must be specified when running classifier!')

        clas9n_repr = PrepParamsParser.to_classification_prep_params(self._repr)
        return os.path.join(DEFAULT_PARSED_DATASETS_DIR, self._dataset, CLASSIFICATION_DIR_NAME,
                            self._classification_type, clas9n_repr)

    @property
    def path_to_classification_model(self):
        return os.path.join(self.path_to_classification_dataset, self._base_model)

    @property
    def path_to_best_base_model(self):
        if not self._base_model:
            raise ValueError("Base model is not set!")

        return os.path.join(self.path_to_lang_model_dataset, self._base_model, MODELS_DIR, f'{self._dataset}_best.h5')

    @property
    def path_to_langmodel(self):
        if not self._model_name:
            raise ValueError("Path to model is not yet created! Call 'create_and_get_path_to_model()' first")

        return os.path.join(self.path_to_lang_model_dataset, self._model_name)

    @property
    def train_path(self):
        return os.path.join(self.path_to_lang_model_dataset, TRAIN_DIR)

    @property
    def test_path(self):
        return os.path.join(self.path_to_lang_model_dataset, TEST_DIR)

    @property
    def valid_path(self):
        return os.path.join(self.path_to_lang_model_dataset, VALID_DIR)

    @property
    def classification_test_path(self):
        return os.path.join(self.path_to_classification_dataset, TEST_DIR)

    @property
    def path_to_langmodel_encoder(self):
        if not self._base_model:
            raise ValueError("Base model is not set!")

        return os.path.join(self.path_to_lang_model_dataset, self._base_model, MODELS_DIR, 'encoder.h5')

    @property
    def path_to_classifier_encoder(self):
        if not self._base_model:
            raise ValueError("Base model is not set!")

        return os.path.join(self.path_to_classification_model, MODELS_DIR, 'lm_encoder.h5')

    ######################################

    def _get_non_existent_model_name(self):
        model_name = self._base_model + "_extratrained"
        while os.path.exists(os.path.join(self.path_to_lang_model_dataset, model_name)):
            model_name = model_name + "_"
        return model_name

    def _get_model_name_by_params(self, data: Data, arch: Arch):
        normalized_percent, normalized_start_from = normalize_percent_data(data.percent, data.start_from)
        percent_prefix = f"{normalized_percent}_{'' if normalized_start_from == '0' else (normalized_start_from + '_')}"
        most_similar_model_name, config_diff = find_most_similar_config(percent_prefix, self.path_to_lang_model_dataset,
                                                                        arch)
        if config_diff == {}:
            model_name = most_similar_model_name
        else:  # nn wasn't run with this config yet
            name = find_name_for_new_config(percent_prefix,
                                            config_diff) if most_similar_model_name is not None else f"{percent_prefix}baseline"
            path_to_model = os.path.join(self.path_to_lang_model_dataset, name)
            while os.path.exists(path_to_model):
                name = name + "_"
                path_to_model = os.path.join(self.path_to_lang_model_dataset, name)
            model_name = name
        return model_name

    def create_and_get_path_to_model(self, data: Data, arch: Arch):
        if self._base_model:
            model_name = self._get_non_existent_model_name()
        else:
            model_name = self._get_model_name_by_params(data, arch)
        self._model_name = model_name
        path_to_model = os.path.join(self.path_to_lang_model_dataset, model_name)
        if not os.path.exists(path_to_model):
            os.makedirs(path_to_model)
        return path_to_model

    def _create_and_get_path_to_classifier(self):
        path_to_classifier_model_models = os.path.join(self.path_to_classification_dataset, self._base_model,
                                                       MODELS_DIR)
        if not os.path.exists(path_to_classifier_model_models):
            os.makedirs(path_to_classifier_model_models)

    def save_vocab_data(self, text_field: Field):
        ####  TODO no need to save vocab data if it's already there in metadata
        # if its not there save t metadata

        io_utils.dump_dict_into_2_columns(text_field.vocab.freqs,
                                          os.path.join(self.path_to_lang_model_dataset, 'vocab_all.txt'))
        pickle.dump(text_field, open(os.path.join(self.path_to_lang_model_dataset, TEXT_FIELD_FILE), 'wb'))

        vocab_size = len(text_field.vocab.itos)
        logger.info(f'Vocabulary size is: {vocab_size}')
        with open(os.path.join(self.path_to_lang_model_dataset, 'vocab_size'), 'w') as f:
            f.write("# This is automatically generated file! Do not edit!\n")
            f.write(str(vocab_size))

        ####

    def model_id(self):
        if not self._model_name:
            raise ValueError("Path to model is not yet created! Call 'create_and_get_path_to_model()' first")

        return f'{self._dataset}.{self.repr}.{self._model_name}'

    def copy_best_base_model(self):
        path_to_model_best_base = os.path.join(self.path_to_classification_model, MODELS_DIR, f'best_base.h5')
        try:
            logger.info(f"Copying from {self.path_to_best_base_model} to {path_to_model_best_base}")
            copyfile(self.path_to_best_base_model, path_to_model_best_base)
        except IOError:
            logger.error("Error copying file!")
            exit(1)

    def save(self, learner):
        learner.save(self._dataset)

    def save_encoder(self, learner):
        learner.save_encoder('encoder')

    def save_best(self, learner):
        learner.save(f'best')

    def load_best(self, learner) -> bool:
        try:
            learner.load('best')
            return True
        except FileNotFoundError:
            logger.info(f"Best model not found")
            return False

    def load_best_base(self, rnn_learner) -> bool:
        try:
            rnn_learner.load(f'{self._dataset}_best_base')
            logger.info("Base model detected and loaded")
            return True
        except FileNotFoundError:
            logger.info(f"Base model not found")
            return False

    def load_text_field(self):
        return pickle.load(open(os.path.join(self.path_to_lang_model_dataset, TEXT_FIELD_FILE), 'rb'))

    def load_pretrained_langmodel(self, rnn_learner: RNN_Learner) -> None:
        logger.info(f"Copying {self.path_to_langmodel_encoder} to {self.path_to_classifier_encoder}")
        shutil.copy(self.path_to_langmodel_encoder, self.path_to_classifier_encoder)
        rnn_learner.load_encoder('lm_encoder')
