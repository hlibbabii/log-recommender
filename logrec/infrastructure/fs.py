import json
import logging
import os
import shutil
from typing import Optional, Union, TypeVar, Type

import dill as pickle

from torchtext.data import Field

from fastai.nlp import RNN_Learner
from logrec.dataprep import MODELS_DIR, TEXT_FIELD_FILE, REPR_DIR, TRAIN_DIR, VALID_DIR, TEST_DIR, \
    CLASSIFICATION_DIR, PARSED_DIR, METADATA_DIR
from logrec.util.io import dump_dict_into_2_columns
from logrec.infrastructure import fractions_manager
from logrec.infrastructure.config_manager import find_most_similar_config, find_name_for_new_config
from logrec.properties import DEFAULT_PARSED_DATASETS_DIR
from logrec.config.model import Data, LMTrainingConfig, ClassifierTrainingConfig, PretrainingType
from logrec.properties import DEFAULT_RAW_DATASETS_DIR
from logrec.util.files import get_two_levels_subdirs

logger = logging.getLogger(__name__)

EXTRATRAINED_SUFFIX = '_extratrained'
BASELINE_NAME = 'baseline'
BEST_MODEL_NAME = 'best'
ENCODER_NAME = 'encoder'
BEST_LOSS_FILENAME = 'loss.best'
BEST_ACC_FILENAME = 'acc.best'
BEST_EPOCH_FILENAME = 'epoch.best'
BEST_BASE_MODEL_NAME = 'best_base'
LM_ENCODER_NAME = 'lm_encoder'
PRETRAINED_MODELS_SEPARATOR = '_-_'
PLOT_FILENAME = 'lr_finder_plot.png'
PP_PARAMS_FILENAME = 'params.json'
PREPROCESSING_TYPES_FILENAME = 'preprocessing_types.json'
LR_FINDING_MODEL_NAME = 'lr_finding'

T = TypeVar('T', bound='FS')


class FS(object):
    def __init__(self, dataset: str, repr: Optional[str],
                 base_dataset: Optional[str] = None, base_model: Optional[str] = None,
                 pretraining: PretrainingType = None,
                 classification_type: Optional[str] = None):
        if bool(base_model) != bool(pretraining):
            raise ValueError('Base model and pretraining_type params must be both set or both unset!')

        self._dataset = dataset
        self._repr = repr

        self._base_dataset = base_dataset
        self._base_model = base_model
        self._pretraining = pretraining

        self._classification_type = classification_type

        self._model_name = None

        # TODO its a dirty hack. fix it
        self.lm_cl_pretraining = None

    #####################################################

    @classmethod
    def for_lang_model(cls: Type[T], dataset: str, repr: str, base_model: str) -> T:
        return cls(dataset, repr, *FS._split_full_model_name(dataset, base_model),
                   PretrainingType.FULL if base_model else None)

    @classmethod
    def for_classifier(cls: Type[T],
                       dataset: str, repr: str, base_model: str,
                       pretraining: PretrainingType, classification_type: str) -> T:
        return cls(dataset, repr, *FS._split_full_model_name(dataset, base_model), pretraining, classification_type)

    @classmethod
    def for_parse_projects(cls: Type[T], dataset: str) -> T:
        fs = cls(dataset, None)
        if not os.path.exists(fs.path_to_parsed_dataset):
            os.makedirs(fs.path_to_parsed_dataset)
        return fs

    #####################################################

    @classmethod
    def _split_full_model_name(cls: Type[T], dataset: str, full_model_name: Optional[str]):
        if not full_model_name:
            return [None, None]

        spl = full_model_name.split("/")
        return spl[0] if len(spl) == 2 else dataset, spl[-1]

    ####################################################

    @property
    def is_lang_model(self) -> bool:
        return not self._classification_type

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
    def base_model_specified(self) -> bool:
        return self._base_model is not None

    @property
    def base_dataset(self) -> str:
        if not self._base_dataset:
            raise ValueError("Base dataset is not set!")

        return self._base_dataset

    @property
    def pretraining(self):
        return self._pretraining

    @property
    def model_name(self) -> str:
        if not self._model_name:
            raise ValueError("Path to model is not yet created! Call 'create_and_get_path_to_model()' first")

        return self._model_name

    @property
    def classification_type(self) -> str:
        if not self._classification_type:
            raise ValueError("Classification type is not set! "
                             "Are you supposed to run a langmodel? "
                             "Did you forget to specify classification_type param when creating FS?")

        return self._classification_type

    @property
    def path_to_lr_plot(self) -> str:
        if not self.is_lang_model:
            raise AssertionError("This method can only be called for lang models.")

        return os.path.join(self.path_to_model, PLOT_FILENAME)

    #################################################333

    @property
    def model_id(self) -> str:
        return f'{self.dataset}.{self.repr}.{self.model_name}'

    @property
    def base_model_id(self) -> str:
        return f'{self.base_dataset}.{self.repr}.{self.base_model}'

    @property
    def path_to_raw_dataset(self) -> str:
        return os.path.join(DEFAULT_RAW_DATASETS_DIR, self.dataset)

    @property
    def path_to_dataset(self) -> str:
        return os.path.join(DEFAULT_PARSED_DATASETS_DIR, self.dataset)

    @property
    def path_to_base_dataset(self) -> str:
        return os.path.join(DEFAULT_PARSED_DATASETS_DIR, self.base_dataset)

    @property
    def path_to_parsed_dataset(self) -> str:
        return os.path.join(self.path_to_dataset, PARSED_DIR)

    @property
    def path_to_metadata(self) -> str:
        return os.path.join(self.path_to_dataset, METADATA_DIR, self.repr)

    @property
    def path_to_base_metadata(self) -> str:
        return os.path.join(self.path_to_base_dataset, METADATA_DIR, self.repr)

    @property
    def path_to_model_dataset(self) -> str:
        return os.path.join(self.path_to_dataset,
                            REPR_DIR if self.is_lang_model else os.path.join(CLASSIFICATION_DIR,
                                                                             self.classification_type),
                            self.repr
                            )

    @property
    def path_to_base_model_dataset(self) -> str:
        return os.path.join(self.path_to_base_dataset,
                            REPR_DIR if (self.is_lang_model or self.lm_cl_pretraining) else os.path.join(
                                CLASSIFICATION_DIR,
                                self.classification_type),
                            self.repr
                            )

    @property
    def path_to_model(self) -> str:
        return os.path.join(self.path_to_model_dataset, self.model_name)

    @property
    def path_to_base_model(self):
        return os.path.join(self.path_to_base_model_dataset, self.base_model)

    @property
    def path_to_base_torch_model(self) -> str:
        return os.path.join(self.path_to_base_model, MODELS_DIR, f'{BEST_MODEL_NAME}.h5')

    @property
    def path_to_base_torch_encoder(self) -> str:
        return os.path.join(self.path_to_base_model, MODELS_DIR, 'encoder.h5')

    @property
    def path_to_models_dir(self):
        path_to_model_dir = os.path.join(self.path_to_model, MODELS_DIR)
        if not os.path.exists(path_to_model_dir):
            os.mkdir(path_to_model_dir)
        return path_to_model_dir

    @property
    def path_to_new_encoder_location(self) -> str:
        return os.path.join(self.path_to_models_dir, 'lm_encoder.h5')

    @property
    def path_to_new_torch_model_location(self):
        return os.path.join(self.path_to_models_dir, f'{BEST_BASE_MODEL_NAME}.h5')

    @property
    def train_path(self) -> str:
        return os.path.join(self.path_to_model_dataset, TRAIN_DIR)

    @property
    def test_path(self) -> str:
        return os.path.join(self.path_to_model_dataset, TEST_DIR)

    @property
    def valid_path(self) -> str:
        return os.path.join(self.path_to_model_dataset, VALID_DIR)

    ######################################

    def _get_non_existent_file_name(self, basename: str) -> str:
        while os.path.exists(os.path.join(self.path_to_model_dataset, basename)):
            basename = basename + "_"
        return basename

    def _get_model_name_by_params(self,
                                  data: Data,
                                  training_config: Union[LMTrainingConfig, ClassifierTrainingConfig]) -> str:

        prefix = ''
        if self.base_model_specified:
            dataset_prefix = f'{self.base_dataset}__' if self.base_dataset != self.dataset else ''
            prefix += f'{dataset_prefix}{self.base_model}{PRETRAINED_MODELS_SEPARATOR}'

        percent_prefix = fractions_manager.get_percent_prefix(data.percent, data.start_from)
        prefix += percent_prefix

        most_similar_model_name, config_diff = find_most_similar_config(prefix, self.path_to_model_dataset,
                                                                        training_config)
        if config_diff == {}:
            logger.info(f'Model with identical params found: {most_similar_model_name}')
            return most_similar_model_name
        else:  # nn wasn't run with this config yet
            name = find_name_for_new_config(prefix, config_diff) \
                if most_similar_model_name is not None \
                else f"{prefix}{BASELINE_NAME}"
            return self._get_non_existent_file_name(name)

    def _create_and_get_path_to_model(self,
                                      data: Data,
                                      training_config: Union[LMTrainingConfig, ClassifierTrainingConfig],
                                      ) -> str:
        if training_config.training is None:
            # lr-finding case, hopefully, temporary hack
            model_name = self._get_non_existent_file_name(LR_FINDING_MODEL_NAME)
        elif self.pretraining == PretrainingType.FULL:
            model_name = self._get_non_existent_file_name(self.base_model + EXTRATRAINED_SUFFIX)
        else:
            model_name = self._get_model_name_by_params(data, training_config)
        path_to_model = os.path.join(self.path_to_model_dataset, model_name)
        if not os.path.exists(path_to_model):
            os.makedirs(path_to_model)
        return model_name

    def create_path_to_model(self, data: Data,
                             training_config: Union[LMTrainingConfig, ClassifierTrainingConfig]) -> None:
        self._model_name = self._create_and_get_path_to_model(data, training_config)

    def save_vocab_data(self, text_field: Field, percent: float, start_from: float) -> None:
        prefix = fractions_manager.get_percent_prefix(percent, start_from)
        dump_dict_into_2_columns(text_field.vocab.freqs,
                                 os.path.join(self.path_to_metadata, f'{prefix}vocab_all.txt'))

    def save_pp_params(self, pp_params):
        with open(os.path.join(self.path_to_parsed_dataset, PP_PARAMS_FILENAME), 'w') as f:
            json.dump(pp_params, f)

    def save_preprocessing_types(self, preprocessing_types):
        with open(os.path.join(self.path_to_parsed_dataset, PREPROCESSING_TYPES_FILENAME), 'w') as f:
            json.dump(preprocessing_types, f)

    def save_best(self, learner):
        learner.save(BEST_MODEL_NAME)

    def load_best(self, learner: RNN_Learner) -> bool:
        try:
            learner.load(BEST_MODEL_NAME)
            return True
        except FileNotFoundError:
            return False

    def best_model_exists(self, learner: RNN_Learner) -> bool:
        return os.path.exists(os.path.join(learner.models_path, f'{BEST_MODEL_NAME}.h5'))

    def load_base_model(self, rnn_learner: RNN_Learner) -> None:
        logger.debug(f"Copying from {self.path_to_base_torch_model} to {self.path_to_new_torch_model_location}")
        shutil.copy(self.path_to_base_torch_model, self.path_to_new_torch_model_location)
        rnn_learner.load(BEST_BASE_MODEL_NAME)

    def load_pretrained_langmodel(self, rnn_learner: RNN_Learner) -> None:
        if self.is_lang_model:
            raise AssertionError("This method can only be called for classifiers.")

        logger.debug(f"Copying {self.path_to_base_torch_encoder} to {self.path_to_new_encoder_location}")
        shutil.copy(self.path_to_base_torch_encoder, self.path_to_new_encoder_location)
        rnn_learner.load_encoder(LM_ENCODER_NAME)

    ###################################

    def get_raw_projects(self):
        for _, train_test_valid, project in get_two_levels_subdirs(self.path_to_raw_dataset):
            yield (train_test_valid, project)

    def load_text_field(self):
        path_to_metadata = self.path_to_base_metadata if self.base_model_specified else self.path_to_metadata
        logger.debug(f'Loading field from {path_to_metadata}')
        return pickle.load(open(os.path.join(path_to_metadata, TEXT_FIELD_FILE), 'rb'))
