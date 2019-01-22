from typing import Union

from torchtext.data import Field

from fastai.nlp import RNN_Learner
from logrec.classifier import classifier
from logrec.classifier.classifier import LEVEL_LABEL
from logrec.langmodel import lang_model
from logrec.cli import preprocess
from logrec.infrastructure import config_manager
from logrec.infrastructure.fs import FS
from logrec.modeltest import to_test_mode, get_predictions, format_predictions
from logrec.param.model import LangmodelTrainingConfig, Pretraining, ClassifierTrainingConfig


class TrainedModel(object):
    def __init__(self, repr: str, fs: FS, text_field: Field, config_class: type,
                 output_field: Field, n_predictions: int):
        self._repr = repr
        self._fs = fs
        self._text_field = text_field
        self._config_class = config_class
        self._output_field = output_field
        self._n_predictions = n_predictions

        self._learner = self.__load_learner()

    @staticmethod
    def for_classifier(dataset: str, repr: str, model: str, classifier_type: str):
        return TrainedClassifier(dataset, repr, model, classifier_type)

    @staticmethod
    def for_langmodel(dataset: str, repr: str, model: str):
        return TrainedLangModel(dataset, repr, model)

    def feed_string(self, input: str, do_preprocessing: bool = True) -> None:
        self.__predict(input, do_preprocessing)

    def feed_file(self, file: str, do_preprocessing: bool = True) -> None:
        with open(file, 'r') as f:
            input = f.read()
        self.__predict(input, do_preprocessing)

    def __load_learner(self) -> RNN_Learner:
        config = config_manager.load_config(self._fs.path_to_base_model)
        if not isinstance(config, self._config_class):
            AssertionError(f'Config loaded should be {self._config_class}!')

        learner = self.create_architecture(self._fs, config)
        self._fs.load_best(learner)
        to_test_mode(learner.model)
        return learner

    def __predict(self, input: str, do_preprocessing: bool) -> None:
        if do_preprocessing:
            prep_input = preprocess(input, self._repr)
            input = " ".join(prep_input)
        print("====================================")
        print(input)
        print("====================================")
        probs, labels = get_predictions(self._learner.model, self._text_field, [input],
                                        self._n_predictions)
        formatted_predictions = format_predictions(probs, labels, self._output_field, None)
        print(formatted_predictions)


class TrainedLangModel(TrainedModel):
    def __init__(self, dataset: str, repr: str, model: str):
        fs = FS.for_lang_model(dataset, repr, model)
        text_field = fs.load_text_field()

        super().__init__(repr=repr,
                         fs=fs,
                         text_field=text_field,
                         config_class=LangmodelTrainingConfig,
                         output_field=text_field,
                         n_predictions=10)

    def create_architecture(self, fs: FS, config: Union[ClassifierTrainingConfig, LangmodelTrainingConfig]):
        return lang_model.create_nn_architecture(fs, config.data, config.arch, 1, config.training.backwards,
                                                 fs.path_to_base_model, self._text_field)


class TrainedClassifier(TrainedModel):
    def __init__(self, dataset: str, repr: str, model: str, classifier_type: str):
        fs = FS.for_classifier(dataset, repr, model, Pretraining.FULL, classifier_type)
        text_field = fs.load_text_field()

        super().__init__(repr=repr,
                         fs=fs,
                         text_field=text_field,
                         config_class=ClassifierTrainingConfig,
                         output_field=LEVEL_LABEL,
                         n_predictions=6 if classifier_type == 'level' else 2)

    def create_architecture(self, fs: FS, config: Union[ClassifierTrainingConfig, LangmodelTrainingConfig]):
        return classifier.create_nn_architecture(fs, self._text_field, LEVEL_LABEL,
                                                 config.data,
                                                 config.arch,
                                                 config.log_coverage_threshold,
                                                 config.context_side,
                                                 fs.path_to_base_model)
