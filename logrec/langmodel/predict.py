import logging
from argparse import ArgumentParser
from logrec.infrastructure import config_manager
from logrec.infrastructure.fs import FS
from logrec.langmodel.lang_model import create_nn_architecture
from logrec.langmodel.utils import to_test_mode, get_predictions, format_predictions
from logrec.properties import DEFAULT_PREDICT_ARGS
from logrec.param.model import LangmodelTrainingConfig, Data

logger = logging.getLogger(__name__)


def predict(dataset: str, repr: str, model: str, input_text: str) -> None:
    fs = FS.for_lang_model(dataset, repr, model)

    config = config_manager.load_config(fs.path_to_base_model)
    if not isinstance(config, LangmodelTrainingConfig):
        AssertionError("LangModelTrainingConfig should have been loaded!")

    learner = create_nn_architecture(fs, config.data, config.arch, 1, config.training.backwards, fs.path_to_base_model)
    fs.load_best(learner)

    to_test_mode(learner.model)

    prepared_input = input_text.rstrip("\n").split(" ")
    probs, labels = get_predictions(learner.model, learner.text_field, [prepared_input], 50)
    formatted_predictions = format_predictions(probs, labels, learner.text_field, "`l")
    logger.info(input_text)
    logger.info(formatted_predictions)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('dataset', action='store', help=f'TODO')
    parser.add_argument('repr', action='store', help='TODO')
    parser.add_argument('model', action='store', help='TODO')
    parser.add_argument('input', action='store', help='TODO')

    args = parser.parse_known_args(*DEFAULT_PREDICT_ARGS)
    args = args[0]

    predict(args.dataset, args.repr, args.model, args.input)
