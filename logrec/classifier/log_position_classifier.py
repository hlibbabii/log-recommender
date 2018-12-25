import logging
from argparse import ArgumentParser
from functools import partial

import numpy as np
import torch
from torchtext import data
from torchtext.data import Field

from fastai.lm_rnn import seq2seq_reg
from fastai.metrics import accuracy
from fastai.nlp import TextData, RNN_Learner
from logrec.classifier.context_datasets import ContextsDataset
from logrec.classifier.dataset_generator import WORDS_IN_CONTEXT_LIMIT
from logrec.infrastructure import config_manager
from logrec.infrastructure.fs import FS, BEST_MODEL_NAME
from logrec.langmodel.lang_model import printGPUInfo
from logrec.langmodel.utils import to_test_mode, output_predictions
from logrec.param.model import Arch, Training
from logrec.param.templates import classifier_training_param
from logrec.util.io_utils import file_mapper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

EXAMPLES_TO_SHOW = 100

LEVEL_LABEL = data.LabelField()
CLASSIFICATION_TYPE = "location"


def get_text_classifier_model(fs: FS, text_field: Field, level_label: Field, arch: Arch, threshold: float):
    splits = ContextsDataset.splits(text_field, level_label, fs.path_to_classification_dataset, threshold=threshold)

    text_data = TextData.from_splits(fs.path_to_classification_model, splits, arch.bs)

    opt_fn = partial(torch.optim.Adam, betas=(0.7, 0.99))

    rnn_learner = text_data.get_model(opt_fn, WORDS_IN_CONTEXT_LIMIT, arch.bptt, arch.em_sz, arch.nh,
                                      arch.nl,
                                      dropouti=arch.drop.outi,
                                      dropout=arch.drop.out,
                                      wdrop=arch.drop.w,
                                      dropoute=arch.drop.oute,
                                      dropouth=arch.drop.outh)

    # reguarizing LSTM paper -- penalizing large activations -- reduce overfitting
    rnn_learner.reg_fn = partial(seq2seq_reg, alpha=arch.reg_fn.alpha, beta=arch.reg_fn.beta)

    logger.info(f'Dictionary size is: {len(text_field.vocab.itos)}')
    logger.info(rnn_learner)

    logger.info("Checking if pretrained classifier exists...")
    model_loaded = fs.load_best(rnn_learner)
    logger.info('Pretrained classifier is found and loaded.')
    if not model_loaded:
        logger.info(f"Pretrained classifier model not found. Loading pretrained langmodel...")
        fs.load_pretrained_langmodel(rnn_learner)

    rnn_learner.clip = 25.

    return rnn_learner, model_loaded


def train(fs: FS, rnn_learner: RNN_Learner, training: Training):
    base_lr = 1e-3
    factor = 2.6
    lrs = np.array([
        base_lr / factor ** 4,
        base_lr / factor ** 3,
        base_lr / factor ** 2,
        base_lr / factor,
        base_lr])

    rnn_learner.freeze_to(-1)
    rnn_learner.fit(lrs, metrics=[accuracy], cycle_len=3, n_cycle=1, cycle_mult=1,
                    best_save_name=BEST_MODEL_NAME,
                    cycle_save_name=''
                    # file=f"{path_to_model}/training.log"
                    )
    # rnn_learner.freeze_to(-2)
    # rnn_learner.fit(lrs, metrics=[accuracy], cycle_len=2, n_cycle=1, cycle_mult=2)
    # rnn_learner.unfreeze()
    # rnn_learner.fit(lrs, metrics=[accuracy], cycle_len=1, n_cycle=1)

    # logger.info(f'Current accuracy is ...')
    # logger.info(f'                    ... {accuracy_gen(*rnn_learner.predict_with_targs())}')
    # rnn_learner.sched.plot_loss()

    fs.save(rnn_learner)

    return rnn_learner


CLASSIFIER_NAME_SUFFIX = "_location_classifier"


def read_lines(filename):
    with open(filename, 'r') as f:
        return f.readlines()


def show_tests(path_to_test_set, m, text_field):
    counter = 0
    for c_filename, l_filename in file_mapper(path_to_test_set, ContextsDataset._get_pair, extension='label'):
        c_file = None
        l_file = None
        try:
            c_file = open(c_filename, 'r')
            l_file = open(l_filename, 'r')
            for context, level in zip(c_file, l_file):
                if counter >= EXAMPLES_TO_SHOW:
                    return
                output_predictions(m, text_field, LEVEL_LABEL, context.rstrip("\n"), 2)
                counter += 1
        except FileNotFoundError:
            project_name = c_filename[:-len(ContextsDataset.FW_CONTEXTS_FILE_EXT)]
            logger.error(f"Project context not loaded: {project_name}")
            continue
        finally:
            if c_file is not None:
                c_file.close()
            if l_file is not None:
                l_file.close()


def run(force_rerun: bool):
    base_model = classifier_training_param.base_model

    fs = FS(classifier_training_param.data.dataset, classifier_training_param.data.repr, base_model,
            classification_type=CLASSIFICATION_TYPE)
    printGPUInfo()

    text_field = fs.load_text_field()
    learner, classifier_model_trained = get_text_classifier_model(fs, text_field, LEVEL_LABEL,
                                                                  classifier_training_param.arch,
                                                                  threshold=classifier_training_param.threshold)

    if classifier_model_trained and not force_rerun:
        logger.info(f'Model {fs.path_to_classification_model} already trained. Not rerunning training.')
        return
    elif classifier_model_trained:
        logger.info(f"Forcing rerun")

    config_manager.save_config(classifier_training_param.training_config, fs.path_to_classification_model)

    train(fs, learner, classifier_training_param.training)

    model = learner.model

    to_test_mode(model)
    show_tests(fs.classification_test_path, model, text_field)

    # plotting confusion matrix
    # preds = np.argmax(probs, axis=1)
    # probs = probs[:,1]
    # from sklearn.metrics import confusion_matrix
    # cm = confusion_matrix(y, preds)
    # plot_confusion_matrix(cm, data.classes)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--force-rerun', action='store_const', const=True, default=False)
    args = parser.parse_args(['--force-rerun'])
    run(args.force_rerun)
