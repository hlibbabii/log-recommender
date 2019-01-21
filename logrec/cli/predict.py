from fastai.nlp import RNN_Learner
from logrec.cli import preprocess
from logrec.infrastructure import config_manager
from logrec.infrastructure.fs import FS
from logrec.langmodel.lang_model import create_nn_architecture
from logrec.langmodel.utils import to_test_mode, get_predictions, format_predictions
from logrec.param.model import LangmodelTrainingConfig


class TrainedLangModel(object):
    def __init__(self, dataset: str, repr: str, model: str):
        self.repr = repr
        self.learner = TrainedLangModel.__load_learner(dataset, repr, model)

    @staticmethod
    def __load_learner(dataset, repr, model) -> RNN_Learner:
        fs = FS.for_lang_model(dataset, repr, model)

        config = config_manager.load_config(fs.path_to_base_model)
        if not isinstance(config, LangmodelTrainingConfig):
            AssertionError("LangModelTrainingConfig should have been loaded!")

        preloaded_text_filed = fs.load_text_field()
        learner = create_nn_architecture(fs, config.data, config.arch, 1, config.training.backwards,
                                         fs.path_to_base_model, preloaded_text_filed)
        fs.load_best(learner)
        to_test_mode(learner.model)
        return learner

    def __predict(self, input: str) -> None:
        prep_input = preprocess(input, self.repr)
        str_to_feed_to_model = " ".join(prep_input)
        print("====================================")
        print(str_to_feed_to_model)
        print("====================================")
        probs, labels = get_predictions(self.learner.model, self.learner.text_field, [str_to_feed_to_model], 50)
        formatted_predictions = format_predictions(probs, labels, self.learner.text_field, None)
        print(formatted_predictions)

    def for_string(self, input: str) -> None:
        self.__predict(input)

    def for_file(self, file: str) -> None:
        with open(file, 'r') as f:
            input = f.read()
        self.__predict(input)
