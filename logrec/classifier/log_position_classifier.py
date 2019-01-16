import logging
import os
from argparse import ArgumentParser
from functools import partial
from time import time
from typing import List

import torch
from torchtext import data
from torchtext.data import Field

from fastai.lm_rnn import seq2seq_reg, SequentialRNN
from fastai import metrics
from fastai.nlp import TextData, RNN_Learner, USE_GPU
from logrec.classifier.context_datasets import ContextsDataset
from logrec.infrastructure import config_manager
from logrec.infrastructure.fs import FS, BEST_MODEL_NAME
from logrec.langmodel.lang_model import printGPUInfo
from logrec.langmodel.utils import to_test_mode, get_predictions, attach_dataset_aware_handlers_to_loggers, \
    format_input, format_predictions
from logrec.param.model import Arch, ClassifierTraining, Data
from logrec.param.templates import classifier_training_param
from logrec.util.io_utils import file_mapper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

EXAMPLES_TO_SHOW = 200

LEVEL_LABEL = data.LabelField()


def create_nn_architecture(fs: FS, text_field: Field, level_label: Field, data: Data, arch: Arch, threshold: float):
    splits = ContextsDataset.splits(text_field, level_label, fs.path_to_classification_dataset, context_len=arch.bptt,
                                    threshold=threshold, data=data)

    text_data = TextData.from_splits(fs.path_to_classification_model, splits, arch.bs)

    opt_fn = partial(torch.optim.Adam, betas=(0.7, 0.99))

    if arch.qrnn and not USE_GPU:
        logger.warning("Cuda not available, not using qrnn. Using lstm instead")
        arch.qrnn = False
    rnn_learner = text_data.get_model(opt_fn, arch.bptt + 1, arch.bptt, arch.em_sz, arch.nh,
                                      arch.nl,
                                      dropouti=arch.drop.outi,
                                      dropout=arch.drop.out,
                                      wdrop=arch.drop.w,
                                      dropoute=arch.drop.oute,
                                      dropouth=arch.drop.outh,
                                      bidir=arch.bidir,
                                      qrnn=arch.qrnn)

    # reguarizing LSTM paper -- penalizing large activations -- reduce overfitting
    rnn_learner.reg_fn = partial(seq2seq_reg, alpha=arch.reg_fn.alpha, beta=arch.reg_fn.beta)

    logger.info(f'Dictionary size is: {len(text_field.vocab.itos)}')
    return rnn_learner


def get_text_classifier_model(fs: FS,
                              text_field: Field,
                              level_label: Field,
                              data: Data,
                              arch: Arch,
                              threshold: float) -> (RNN_Learner, bool):
    rnn_learner = create_nn_architecture(fs, text_field, level_label, data, arch, threshold)
    logger.info(rnn_learner)

    logger.info("Checking if there exists a model with the same architecture")
    model_loaded = fs.load_best(rnn_learner)
    if not model_loaded and fs.base_model_present:
        # checking if there is a base model and trying to load it
        base_model_loaded = fs.load_best_base_classifier(rnn_learner)
        if not base_model_loaded:
            logger.info("Not using base model. Loading pretrained lang model...")
            fs.load_pretrained_langmodel(rnn_learner)

    rnn_learner.clip = 25.

    return rnn_learner, model_loaded


def train(fs: FS, rnn_learner: RNN_Learner, training: ClassifierTraining):
    training_log_file = os.path.join(fs.path_to_classification_model, 'training.log')
    if not training.stages:
        logger.warning("No stages specified in the config")
        return
    training_start_time = time()
    logger.info(f"Starting training, check {training_log_file} for training progress")
    for stage in training.stages:
        cycle = stage.cycle
        only_validation = False
        n = cycle.n
        if cycle.n == 0 or cycle.len == 0:
            logger.warning("Number of epochs specified at this stage is 0. Not training...")
            only_validation = True
            n = 1

        rnn_learner.freeze_to(stage.freeze_to)
        vals, ep_vals = rnn_learner.fit(lrs=training.lrs,
                                        metrics=list(map(lambda x: getattr(metrics, x), training.metrics)),
                                        wds=training.wds,
                                        cycle_len=cycle.len, n_cycle=n, cycle_mult=cycle.mult,
                                        best_save_name=BEST_MODEL_NAME, cycle_save_name='', get_ep_vals=True,
                                        file=open(training_log_file, 'w+'), only_validation=only_validation
                                        )
        training_time_mins = int(time() - training_start_time) // 60
        with open(os.path.join(fs.path_to_classification_model, 'results.out'), 'w') as f:
            f.write(str(training_time_mins) + "\n")
            for _, vals in ep_vals.items():
                f.write(" ".join(map(lambda x: str(x), vals)) + "\n")

    # logger.info(f'Current accuracy is ...')
    # logger.info(f'                    ... {accuracy_gen(*rnn_learner.predict_with_targs())}')
    # rnn_learner.sched.plot_loss()

    fs.save(rnn_learner)

    return rnn_learner


def read_lines(filename):
    with open(filename, 'r') as f:
        return f.readlines()


def prepare_input(context_before: str, context_after: str) -> List[str]:
    context_after_reversed = context_after.split(" ")
    context_after_reversed.reverse()

    words = [context_before.split(" ")] + [context_after_reversed]
    return words


def show_tests(path_to_test_set: str, model: SequentialRNN, text_field: Field, sample_test_runs_file: str) -> None:
    logger.info("================    Running tests ============")
    counter = 0
    text = ""
    stop_showing_examples = False
    for c_filename_before, c_filename_after, l_filename in file_mapper(path_to_test_set, ContextsDataset._get_pair,
                                                                       extension='label'):
        if stop_showing_examples:
            break
        c_file_before = None
        c_file_after = None
        l_file = None
        try:
            c_file_before = open(c_filename_before, 'r')
            c_file_after = open(c_filename_after, 'r')
            l_file = open(l_filename, 'r')
            for context_before, context_after, label in zip(c_file_before, c_file_after, l_file):
                if label.rstrip('\n') == '':
                    continue

                if counter >= EXAMPLES_TO_SHOW:
                    stop_showing_examples = True
                    break

                context_before = context_before.rstrip("\n")
                context_after = context_after.rstrip("\n")
                prepared_input = prepare_input(context_before, context_after)
                formatted_input = format_input(context_before, context_after)
                probs, labels = get_predictions(model, text_field, prepared_input, 2)
                formatted_predictions = format_predictions(probs, labels, LEVEL_LABEL, label.rstrip("\n"))
                logger.info(formatted_input + formatted_predictions)
                text += (formatted_input + formatted_predictions)
                counter += 1
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
    logger.info(f"Saving test output to {sample_test_runs_file}")
    with open(sample_test_runs_file, 'w') as f:
        f.write(text)


def run_on_device(classifier: str, force_rerun: bool) -> None:
    base_model = classifier_training_param.base_model
    pretrained_model = classifier_training_param.pretrained_model

    fs = FS.for_classifier(classifier_training_param.data.dataset, classifier_training_param.data.repr,
                           base_model=base_model, pretrained_model=pretrained_model,
                           classification_type=classifier)

    fs.create_path_to_classifier(classifier_training_param.data, classifier_training_param.classifier_training_config)
    attach_dataset_aware_handlers_to_loggers(fs.path_to_classification_model, 'main.log')

    printGPUInfo()

    text_field = fs.load_text_field()
    learner, classifier_model_trained = get_text_classifier_model(fs, text_field, LEVEL_LABEL,
                                                                  classifier_training_param.data,
                                                                  classifier_training_param.arch,
                                                                  threshold=classifier_training_param.threshold)

    if classifier_model_trained and not force_rerun:
        logger.info(f'Model {fs.path_to_classification_model} already trained. Not rerunning training.')
        return
    elif classifier_model_trained:
        logger.info(f"Forcing rerun")

    config_manager.save_config(classifier_training_param.classifier_training_config, fs.path_to_classification_model)

    train(fs, learner, classifier_training_param.classifier_training)

    model = learner.model

    to_test_mode(model)
    sample_test_runs_file = os.path.join(fs.path_to_classification_model, 'test_runs.out')
    show_tests(fs.classification_test_path, model, text_field, sample_test_runs_file)
    logger.info("Classifier training finished successfully.")

    # plotting confusion matrix
    # preds = np.argmax(probs, axis=1)
    # probs = probs[:,1]
    # from sklearn.metrics import confusion_matrix
    # cm = confusion_matrix(y, preds)
    # plot_confusion_matrix(cm, data.classes)


def run(classifier: str, force_rerun: bool) -> None:
    if USE_GPU:
        with(classifier_training_param.device):
            run_on_device(classifier, force_rerun)
    else:
        run_on_device(classifier, force_rerun)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--force-rerun', action='store_const', const=True, default=False)
    parser.add_argument('classifier', action='store')
    args = parser.parse_args()
    run(args.classifier, args.force_rerun)
