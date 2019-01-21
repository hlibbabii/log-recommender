from logrec.infrastructure import config_manager
from logrec.infrastructure.fs import FS
from logrec.langmodel.lang_model import create_nn_architecture
from logrec.langmodel.utils import to_test_mode, get_predictions, format_predictions
from logrec.param.model import LangmodelTrainingConfig


class TrainedLangModel(object):
    def __init__(self, dataset: str, repr: str, model: str):
        fs = FS.for_lang_model(dataset, repr, model)

        config = config_manager.load_config(fs.path_to_base_model)
        if not isinstance(config, LangmodelTrainingConfig):
            AssertionError("LangModelTrainingConfig should have been loaded!")

        preloaded_text_filed = fs.load_text_field()
        self.learner = create_nn_architecture(fs, config.data, config.arch, 1, config.training.backwards,
                                              fs.path_to_base_model, preloaded_text_filed)
        fs.load_best(self.learner)
        to_test_mode(self.learner.model)

    def __predict(self, input: str) -> None:
        prepared_input = input.rstrip("\n").split(" ")
        probs, labels = get_predictions(self.learner.model, self.learner.text_field, [prepared_input], 50)
        formatted_predictions = format_predictions(probs, labels, self.learner.text_field, "`l")
        print(formatted_predictions)

    def for_string(self, input: str) -> None:
        self.__predict(input)

    def for_file(self, file: str) -> None:
        with open(file, 'r') as f:
            input = f.read()
        print("====================================")
        print(input)
        print("====================================")
        self.__predict(input)
