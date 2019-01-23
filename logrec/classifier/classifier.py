import logging
import os
from argparse import ArgumentParser
from functools import partial
from time import time
from typing import List, Optional

import torch
from torch.cuda import device
from torchtext import data
from torchtext.data import Field

from fastai.lm_rnn import seq2seq_reg, SequentialRNN
from fastai import metrics
from fastai.nlp import TextData, RNN_Learner
from logrec.classifier.context_datasets import ContextsDataset
from logrec.dataprep.text_beautifier import beautify_text
from logrec.infrastructure import config_manager
from logrec.infrastructure.fs import FS, BEST_MODEL_NAME
from logrec.langmodel.lang_model import LAST_MODEL_NAME
from logrec.modeltest import to_test_mode, get_predictions, format_predictions
from logrec.misc import attach_dataset_aware_handlers_to_loggers
from logrec.param.model import Arch, ClassifierTraining, Data, ClassifierTrainingParams, Pretraining, ContextSide
from logrec.util import gpu
from logrec.util.files import file_mapper
from logrec.util.gpu import print_gpu_info, get_current_device
from logrec.util.util import get_params_module

logger = logging.getLogger(__name__)

EXAMPLES_TO_SHOW = 200

LEVEL_LABEL = data.LabelField()


def create_nn_architecture(fs: FS, text_field: Field, level_label: Field, data: Data, arch: Arch, threshold: float,
                           context_side: str, path: str = None):
    splits = ContextsDataset.splits(text_field, level_label, fs.path_to_model_dataset, context_len=arch.bptt,
                                    threshold=threshold, data=data, side=context_side)

    text_data = TextData.from_splits(fs.path_to_model if not path else path, splits, arch.bs)

    opt_fn = partial(torch.optim.Adam, betas=(0.7, 0.99))

    if arch.qrnn and not gpu.gpu_available():
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
    rnn_learner.clip = 25.

    logger.info(f'Dictionary size is: {len(text_field.vocab.itos)}')
    return rnn_learner


def train(fs: FS, rnn_learner: RNN_Learner, training: ClassifierTraining):
    training_log_file = os.path.join(fs.path_to_model, 'training.log')
    if not training.stages:
        logger.warning("No stages specified in the config")
        return
    logger.info(f"Starting training, check {training_log_file} for training progress")
    for stage in training.stages:
        training_start_time = time()
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
        with open(os.path.join(fs.path_to_model, 'results.out'), 'a+') as f:
            f.write(str(training_time_mins) + "\n")
            for _, vals in ep_vals.items():
                f.write(" ".join(map(lambda x: str(x), vals)) + "\n")

    # logger.info(f'Current accuracy is ...')
    # logger.info(f'                    ... {accuracy_gen(*rnn_learner.predict_with_targs())}')
    # rnn_learner.sched.plot_loss()

    rnn_learner.save(LAST_MODEL_NAME)

    return rnn_learner


def read_lines(filename):
    with open(filename, 'r') as f:
        return f.readlines()


def prepare_input(context_before: str, context_after: str, side: ContextSide) -> List[List[str]]:
    context_before_list = context_before.split(" ")
    context_after_list = context_after.split(" ")
    context_after_list.reverse()

    if side == ContextSide.BEFORE:
        words = context_before_list
    elif side == ContextSide.AFTER:
        words = context_after_list
    elif side == ContextSide.BOTH:
        words = context_before_list + context_after_list
    else:
        raise AssertionError(f'Unknown side: {side}')
    return [words]


def show_tests(path_to_test_set: str, model: SequentialRNN, text_field: Field,
               sample_test_runs_file: str, context_side: ContextSide, n_predictions: int) -> None:
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
                prepared_input = prepare_input(context_before, context_after, context_side)
                formatted_input = format_input(context_before, context_after, context_side)
                probs, labels = get_predictions(model, text_field, prepared_input, n_predictions)
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


def format_input(context_before: str, context_after: str, side: str) -> str:
    text = ("===================" + "\n")
    if side in [ContextSide.BEFORE, ContextSide.BOTH]:
        text += (beautify_text(context_before) + "\n")
    if side in [ContextSide.AFTER, ContextSide.BOTH]:
        text += "\n"
        text += (beautify_text(context_after) + "\n")
    text += ("===================" + "\n")
    if side in [ContextSide.BEFORE, ContextSide.BOTH]:
        text += (context_before + "\n")
        text += "\n"
    if side in [ContextSide.AFTER, ContextSide.BOTH]:
        text += (context_after + "\n")
    return text

def run_on_device(classifier_training_param: ClassifierTrainingParams, force_rerun: bool) -> None:
    base_model = classifier_training_param.base_model
    pretraining = classifier_training_param.pretraining

    if bool(base_model) != bool(pretraining):
        raise ValueError('Base model and pretraining params must be both set or both unset!')

    fs = FS.for_classifier(classifier_training_param.data.dataset, classifier_training_param.data.repr,
                           base_model=base_model, pretraining=pretraining,
                           classification_type=classifier_training_param.classification_type)

    fs.create_path_to_model(classifier_training_param.data, classifier_training_param.classifier_training_config)
    attach_dataset_aware_handlers_to_loggers(fs.path_to_model, 'main.log')

    print_gpu_info()

    text_field = fs.load_text_field()

    rnn_learner = create_nn_architecture(fs, text_field, LEVEL_LABEL,
                                         classifier_training_param.data,
                                         classifier_training_param.arch,
                                         classifier_training_param.log_coverage_threshold,
                                         classifier_training_param.context_side)
    logger.info(rnn_learner)

    same_model_exists = fs.best_model_exists(rnn_learner)
    if same_model_exists and not force_rerun:
        logger.info(f'Model {fs.path_to_classification_model} already trained. Not rerunning training.'
                    f'To retrain the model with this parameters, specify --force-rerun flag')
        return
    elif same_model_exists:
        logger.info(f"Model {fs.path_to_classification_model} already trained. Forcing rerun.")

    if pretraining == Pretraining.FULL:
        try:
            logger.info(f'Trying to load base classifier: {base_model}')
            fs.load_base_model(rnn_learner)
            logger.info('Base classifier model is loaded.')
        except Exception as e:
            logger.warning(e)
            logger.warning('Base classifier model not loaded. Training from scratch')

    elif pretraining == Pretraining.ONLY_ENCODER:
        try:
            logger.info(f'Trying to load pretarined LM: {base_model}')
            # TODO its a dirty hack. fix it
            fs.lm_cl_pretraining = True
            fs.load_pretrained_langmodel(rnn_learner)
            logger.info("Using pretrained LM")
        except Exception as e:
            logger.warning(e)
            logger.warning('Pretrained LM not loaded. Training from scratch')
    else:
        logger.info("No pretraining. Training classifier from scratch.")

    config_manager.save_config(classifier_training_param.classifier_training_config, fs.path_to_model)

    train(fs, rnn_learner, classifier_training_param.classifier_training)

    model = rnn_learner.model

    to_test_mode(model)
    sample_test_runs_file = os.path.join(fs.path_to_model, 'test_runs.out')
    n_predicitions = 6 if classifier_training_param.classification_type == 'level' else 2
    show_tests(fs.test_path, model, text_field, sample_test_runs_file,
               classifier_training_param.context_side, n_predicitions)
    logger.info("Classifier training finished successfully.")

    # plotting confusion matrix
    # preds = np.argmax(probs, axis=1)
    # probs = probs[:,1]
    # from sklearn.metrics import confusion_matrix
    # cm = confusion_matrix(y, preds)
    # plot_confusion_matrix(cm, data.classes)


def run(force_rerun: bool, params_path: Optional[str], device_id: Optional[int]) -> None:
    module = get_params_module(params_path)
    if gpu.gpu_available():
        gpu_id_to_use = device_id if device_id is not None else get_current_device()
        logger.debug(f'Using gpu with id: {gpu_id_to_use}')
        with device(gpu_id_to_use):
            run_on_device(module.classifier_training_param, force_rerun)
    else:
        run_on_device(module.classifier_training_param, force_rerun)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--force-rerun', action='store_const', const=True, default=False)
    parser.add_argument('--params-path', action='store', help='TODO')
    parser.add_argument('--device', action='store', type=int, help='TODO')
    args = parser.parse_args()
    run(args.force_rerun, args.params_path, args.device)
