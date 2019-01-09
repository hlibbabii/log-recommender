import json
import logging
import os
import shutil
from typing import Optional, Union, TypeVar, Type

import dill as pickle
from shutil import copyfile

from torchtext.data import Field

from fastai.nlp import RNN_Learner
from logrec.dataprep import MODELS_DIR, TEXT_FIELD_FILE, REPR_DIR, TRAIN_DIR, VALID_DIR, TEST_DIR, \
    CLASSIFICATION_DIR, PARSED_DIR
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser
from logrec.infrastructure.config_manager import find_most_similar_config, find_name_for_new_config
from logrec.infrastructure.fractions_manager import normalize_percent_data
from logrec.properties import DEFAULT_PARSED_DATASETS_DIR
from logrec.param.model import Data, LangmodelTrainingConfig, ClassifierTrainingConfig
from logrec.util import io_utils
from logrec.properties import DEFAULT_RAW_DATASETS_DIR

logger = logging.getLogger(__name__)

EXTRATRAINED_SUFFIX = '_extratrained'
BASELINE_NAME = 'baseline'
BEST_MODEL_NAME = 'best'
BEST_BASE_MODEL_NAME = 'best_base'
ENCODER_NAME = 'encoder'
LM_ENCODER_NAME = 'lm_encoder'
LAST_MODEL_NAME = 'last'
PRETRAINED_MODELS_SEPARATOR = '_-_'
PLOT_FILENAME = 'lr_finder_plot.png'
PP_PARAMS_FILENAME = 'params.json'
PREPROCESSING_TYPES_FILENAME = 'preprocessing_types.json'
LR_FINDING_MODEL_NAME = 'lr_finding'


def get_two_levels_subdirs(dir):
    subdirs = next(os.walk(dir))[1]
    for subdir in subdirs:
        for subsubdir in next(os.walk(os.path.join(dir, subdir)))[1]:
            yield dir, subdir, subsubdir


T = TypeVar('T', bound='TrivialClass')


class FS(object):
    def __init__(self, dataset: str, repr: Optional[str], base_model: Optional[str],
                 pretrained_model: Optional[str] = None, classification_type: Optional[str] = None):
        self._dataset = dataset
        self._repr = repr
        self._base_model = base_model
        self._pretrained_model = pretrained_model
        self._classification_type = classification_type

        self._langmodel_name = None
        self._classification_model_name = None

    #####################################################

    @classmethod
    def for_lang_model(cls: Type[T], dataset: str, repr: str, base_model: str) -> T:
        return cls(dataset, repr, base_model)

    @classmethod
    def for_classifier(cls: Type[T], dataset: str, repr: str, base_model: str,
                       pretrained_model: str, classification_type: str) -> T:
        return cls(dataset, repr, base_model, pretrained_model, classification_type)

    @classmethod
    def for_parse_projects(cls: Type[T], dataset: str) -> T:
        fs = cls(dataset, None, None)
        if not os.path.exists(fs.path_to_parsed_dataset):
            os.makedirs(fs.path_to_parsed_dataset)
        return fs

    #####################################################

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def repr(self) -> str:
        return self._repr

    @property
    def base_model(self) -> str:
        if not self._base_model:
            raise ValueError('Base model is not set!')

        return self._base_model

    @property
    def base_model_present(self) -> bool:
        return self._base_model is not None

    @property
    def pretrained_model(self) -> str:
        if not self._pretrained_model:
            raise ValueError("Pretrained model is not set")

        return self._pretrained_model

    @property
    def langmodel_name(self) -> str:
        if not self._langmodel_name:
            raise ValueError("Path to model is not yet created! Call 'create_and_get_path_to_model()' first")

        return self._langmodel_name

    @property
    def classification_type(self) -> str:
        if not self._classification_type:
            raise ValueError("Classification type is not set! "
                             "Are you supposed to run a langmodel? "
                             "Did you forget to specify classification_type param when creating FS?")

        return self._classification_type

    @property
    def classification_model_name(self) -> str:
        if not self._classification_model_name:
            raise ValueError("")

        return self._classification_model_name

    @property
    def path_to_lr_plot(self) -> str:
        return os.path.join(self.path_to_langmodel, PLOT_FILENAME)

    #################################################333

    @property
    def path_to_raw_dataset(self) -> str:
        return os.path.join(DEFAULT_RAW_DATASETS_DIR, self.dataset)

    @property
    def path_to_dataset(self) -> str:
        return os.path.join(DEFAULT_PARSED_DATASETS_DIR, self.dataset)

    @property
    def path_to_parsed_dataset(self) -> str:
        return os.path.join(self.path_to_dataset, PARSED_DIR)

    @property
    def path_to_lang_model_dataset(self) -> str:
        return os.path.join(self.path_to_dataset, REPR_DIR, self.repr)

    @property
    def path_to_classification_dataset(self) -> str:
        clas9n_repr = PrepParamsParser.to_classification_prep_params(self.repr)
        return os.path.join(self.path_to_dataset, CLASSIFICATION_DIR,
                            self.classification_type, clas9n_repr)

    @property
    def path_to_classification_model(self) -> str:
        return os.path.join(self.path_to_classification_dataset, self.classification_model_name)

    def get_path_to_best_base_model(self, path_to_dataset) -> str:
        path_to_base_model = os.path.join(path_to_dataset, self.base_model)
        if not os.path.exists(path_to_base_model):
            logger.error(f'Base model {self.base_model} does not exist')
            exit(321)

        return os.path.join(path_to_base_model, MODELS_DIR, f'{BEST_MODEL_NAME}.h5')

    @property
    def path_to_langmodel(self) -> str:
        return os.path.join(self.path_to_lang_model_dataset, self.langmodel_name)

    @property
    def train_path(self) -> str:
        return os.path.join(self.path_to_lang_model_dataset, TRAIN_DIR)

    @property
    def test_path(self) -> str:
        return os.path.join(self.path_to_lang_model_dataset, TEST_DIR)

    @property
    def valid_path(self) -> str:
        return os.path.join(self.path_to_lang_model_dataset, VALID_DIR)

    @property
    def classification_test_path(self) -> str:
        return os.path.join(self.path_to_classification_dataset, TEST_DIR)

    @property
    def path_to_langmodel_encoder(self) -> str:
        return os.path.join(self.path_to_lang_model_dataset, self.pretrained_model, MODELS_DIR, 'encoder.h5')

    @property
    def path_to_classifier_encoder(self) -> str:
        return os.path.join(self.path_to_classification_model, MODELS_DIR, 'lm_encoder.h5')

    ######################################

    @staticmethod
    def _get_non_existent_file_name(path_to_dataset: str, basename: str) -> str:
        while os.path.exists(os.path.join(path_to_dataset, basename)):
            basename = basename + "_"
        return basename

    @staticmethod
    def _get_model_name_by_params(path_to_dataset: str,
                                  data: Data,
                                  training_config: Union[LangmodelTrainingConfig or ClassifierTrainingConfig],
                                  pretrained_model: Optional[str]) -> str:
        normalized_percent, normalized_start_from = normalize_percent_data(data.percent, data.start_from)
        percent_prefix = f"{normalized_percent}_{'' if normalized_start_from == '0' else (normalized_start_from + '_')}"

        if pretrained_model:  # it it's a classifier
            if not pretrained_model.startswith(percent_prefix):
                raise AssertionError("")
            prefix = f'{pretrained_model}{PRETRAINED_MODELS_SEPARATOR}'
        else:
            prefix = percent_prefix

        most_similar_model_name, config_diff = find_most_similar_config(prefix, path_to_dataset, training_config)
        if config_diff == {}:
            logger.info(f'Model with identical params found: {most_similar_model_name}')
            return most_similar_model_name
        else:  # nn wasn't run with this config yet
            name = find_name_for_new_config(prefix, config_diff) \
                if most_similar_model_name is not None \
                else f"{prefix}{BASELINE_NAME}"
            return FS._get_non_existent_file_name(path_to_dataset, name)

    def create_and_get_path_to_model(self, path_to_dataset: str,
                                     data: Data,
                                     training_config: Union[LangmodelTrainingConfig or ClassifierTrainingConfig],
                                     base_model: str) -> str:
        if training_config.training is None:
            # lr-finding case, hopefully, temporary hack
            model_name = FS._get_non_existent_file_name(path_to_dataset, LR_FINDING_MODEL_NAME)
        elif base_model:
            model_name = FS._get_non_existent_file_name(path_to_dataset, base_model + EXTRATRAINED_SUFFIX)
        else:
            model_name = FS._get_model_name_by_params(path_to_dataset, data, training_config, self._pretrained_model)
        path_to_model = os.path.join(path_to_dataset, model_name)
        if not os.path.exists(path_to_model):
            os.makedirs(path_to_model)
        return model_name

    def create_path_to_langmodel(self, data: Data, langmodel_training_config: LangmodelTrainingConfig) -> None:
        self._langmodel_name = self.create_and_get_path_to_model(self.path_to_lang_model_dataset, data,
                                                                 langmodel_training_config, self._base_model)

    def create_path_to_classifier(self, data: Data, classifier_training_config: ClassifierTrainingConfig) -> None:
        self._classification_model_name = self.create_and_get_path_to_model(self.path_to_classification_dataset, data,
                                                                            classifier_training_config,
                                                                            self._base_model)

    def save_vocab_data(self, text_field: Field) -> None:
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

    def model_id(self) -> str:
        return f'{self.dataset}.{self.repr}.{self.langmodel_name}'

    def _copy_best_base_model(self, path_to_dataset, new_model_name) -> None:
        path_to_model_models = os.path.join(path_to_dataset, new_model_name, MODELS_DIR)
        if not os.path.exists(path_to_model_models):
            os.mkdir(path_to_model_models)
        to_model = os.path.join(path_to_model_models, f'{BEST_BASE_MODEL_NAME}.h5')
        from_model = self.get_path_to_best_base_model(path_to_dataset)
        try:
            logger.info(f"Copying from {from_model} to {to_model}")
            copyfile(from_model, to_model)
        except IOError as err:
            logger.error("Error copying file!")
            raise err

    def save_pp_params(self, pp_params):
        with open(os.path.join(self.path_to_parsed_dataset, PP_PARAMS_FILENAME), 'w') as f:
            json.dump(pp_params, f)

    def save_preprocessing_types(self, preprocessing_types):
        with open(os.path.join(self.path_to_parsed_dataset, PREPROCESSING_TYPES_FILENAME), 'w') as f:
            json.dump(preprocessing_types, f)

    def save(self, learner):
        learner.save(LAST_MODEL_NAME)

    def save_encoder(self, learner):
        learner.save_encoder(ENCODER_NAME)

    def save_best(self, learner):
        learner.save(BEST_MODEL_NAME)

    def load_best(self, learner: RNN_Learner) -> bool:
        try:
            learner.load(BEST_MODEL_NAME)
            return True
        except FileNotFoundError:
            return False

    def load_best_base_langmodel(self, rnn_learner: RNN_Learner) -> bool:
        self._copy_best_base_model(self.path_to_lang_model_dataset, self.langmodel_name)
        try:
            rnn_learner.load(BEST_BASE_MODEL_NAME)
            logger.info("Base model detected and loaded")
            return True
        except FileNotFoundError:
            return False

    def load_best_base_classifier(self, rnn_learner: RNN_Learner) -> bool:
        self._copy_best_base_model(self.path_to_classification_dataset, self.classification_model_name)
        try:
            rnn_learner.load(BEST_BASE_MODEL_NAME)
            logger.info("Base model detected and loaded")
            return True
        except FileNotFoundError:
            return False

    def load_text_field(self):
        return pickle.load(open(os.path.join(self.path_to_lang_model_dataset, TEXT_FIELD_FILE), 'rb'))

    def load_pretrained_langmodel(self, rnn_learner: RNN_Learner) -> None:
        logger.info(f"Copying {self.path_to_langmodel_encoder} to {self.path_to_classifier_encoder}")
        shutil.copy(self.path_to_langmodel_encoder, self.path_to_classifier_encoder)
        rnn_learner.load_encoder(LM_ENCODER_NAME)

    def get_raw_projects(self):
        for _, train_test_valid, project in get_two_levels_subdirs(self.path_to_raw_dataset):
            yield (train_test_valid, project)
