import logging
import os
from argparse import ArgumentParser
from functools import partial
from time import time
from typing import List, Optional

import jsons
import torch
from torch.cuda import device
from torchtext import data
from torchtext.data import Field

from fastai.lm_rnn import seq2seq_reg, SequentialRNN
from fastai import metrics
from fastai.nlp import TextData, RNN_Learner
from logrec.classifier.context_datasets import ContextsDataset
from logrec.config.patch import patch_config
from logrec.dataprep.prepconfig import PrepConfig
from logrec.dataprep.text_beautifier import beautify_text
from logrec.features.early_stop import EarlyStopping
from logrec.infrastructure import config_manager
from logrec.infrastructure.fs import FS, BEST_MODEL_NAME, BEST_LOSS_FILENAME, BEST_ACC_FILENAME, BEST_EPOCH_FILENAME
from logrec.modeltest import to_test_mode, get_predictions, format_predictions
from logrec.misc import attach_dataset_aware_handlers_to_loggers
from logrec.config.model import Arch, ClassifierTraining, Data, ClassifierConfig, PretrainingType
from logrec.util import gpu
from logrec.util.files import file_mapper
from logrec.util.gpu import print_gpu_info, get_current_device
from logrec.util.util import get_params_module

logger = logging.getLogger(__name__)

LEVEL_LABEL = data.LabelField()


def create_nn_architecture(fs: FS, text_field: Field, level_label: Field, data: Data, arch: Arch, threshold: float,
                           path: str = None):
    splits = ContextsDataset.splits(text_field, level_label, fs.path_to_model_dataset, context_len=arch.bptt,
                                    threshold=threshold, data=data)

    text_data = TextData.from_splits(fs.path_to_model if not path else path, splits, arch.bs)

    opt_fn = partial(torch.optim.Adam, betas=(0.7, 0.99))

    if arch.qrnn and not gpu.gpu_available():
        logger.warning("Cuda not available, not using qrnn. Using lstm instead")
        arch.qrnn = False
    dropout_multiplier = arch.drop.multiplier
    rnn_learner = text_data.get_model(opt_fn, arch.bptt + 1, arch.bptt, arch.em_sz, arch.nh,
                                      arch.nl,
                                      dropout=arch.drop.out * dropout_multiplier,
                                      dropouti=arch.drop.outi * dropout_multiplier,
                                      wdrop=arch.drop.w * dropout_multiplier,
                                      dropoute=arch.drop.oute * dropout_multiplier,
                                      dropouth=arch.drop.outh * dropout_multiplier,
                                      bidir=arch.bidir,
                                      qrnn=arch.qrnn)

    # reguarizing LSTM paper -- penalizing large activations -- reduce overfitting
    rnn_learner.reg_fn = partial(seq2seq_reg, alpha=arch.reg_fn.alpha, beta=arch.reg_fn.beta)
    rnn_learner.clip = arch.clip

    logger.info(f'Dictionary size is: {len(text_field.vocab.itos)}')
    return rnn_learner


def train(fs: FS, rnn_learner: RNN_Learner, training: ClassifierTraining, metric_list: List[str]):
    training_log_file = os.path.join(fs.path_to_model, 'training.log')
    if not training.stages:
        logger.warning("No stages specified in the config")
        return
    logger.info(f"Starting training, check {training_log_file} for training progress")
    for idx, stage in enumerate(training.stages):
        training_start_time = time()
        logger.info(f'----- Running stage {idx}')
        cycle = stage.cycle
        only_validation = False
        n = cycle.n
        if cycle.n == 0 or cycle.len == 0:
            logger.warning("Number of epochs specified at this stage is 0. Not training...")
            only_validation = True
            n = 1

        callbacks = []

        if training.early_stop:
            name_suffix = f'.{idx}' if idx < len(training.stages) - 1 else ''
            callbacks.append(EarlyStopping(rnn_learner,
                                           save_path=BEST_MODEL_NAME + name_suffix,
                                           best_loss_path=BEST_LOSS_FILENAME + name_suffix,
                                           best_acc_path=BEST_ACC_FILENAME + name_suffix,
                                           best_epoch_path=BEST_EPOCH_FILENAME + name_suffix,
                                           ))

        rnn_learner.freeze_to(stage.freeze_to)
        lrs = training.lrs
        lr_list = [lrs.base_lr / lrs.factor ** m for m in lrs.multipliers]
        logger.debug(f'Using the following learning rates: {lr_list}')
        vals, ep_vals = rnn_learner.fit(lrs=lr_list,
                                        metrics=list(map(lambda x: getattr(metrics, x), metric_list)),
                                        wds=training.wds,
                                        cycle_len=cycle.len, n_cycle=n, cycle_mult=cycle.mult,
                                        callbacks=callbacks,
                                        get_ep_vals=True,
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

    return rnn_learner


def prepare_input(context_before: str, context_after: str, backwards: bool) -> List[List[str]]:
    if backwards:
        words = context_after.split(" ")
        words.reverse()
    else:
        words = context_before.split(" ")

    return [words]


def show_tests(path_to_test_set: str, model: SequentialRNN, text_field: Field,
               sample_test_runs_file: str, backwards: bool,
               n_predictions: int, n_samples: int) -> None:
    logger.info("================    Running tests ============")
    counter = 0
    text = ""
    stop_showing_examples = False
    for c_filename_before, c_filename_after, l_filename in file_mapper(path_to_test_set, ContextsDataset._get_pair,
                                                                       lambda fi: fi.endswith('label')):
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

                if counter >= n_samples:
                    stop_showing_examples = True
                    break

                context_before = context_before.rstrip("\n")
                context_after = context_after.rstrip("\n")
                prepared_input = prepare_input(context_before, context_after, backwards)
                formatted_input = format_input(context_before, context_after, backwards)
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


def format_input(context_before: str, context_after: str, backwards: bool) -> str:
    text = ("===================" + "\n")
    if not backwards:
        text += (beautify_text(context_before) + "\n")
    else:
        text += "\n"
        text += (beautify_text(context_after) + "\n")
    text += ("===================" + "\n")
    if not backwards:
        text += (context_before + "\n")
        text += "\n"
    else:
        text += (context_after + "\n")
    return text


def run_on_device(config: ClassifierConfig, force_rerun: bool) -> None:
    base_model = config.base_model
    pretraining = config.pretraining_type

    PrepConfig.assert_classification_config(config.data.repr)

    if bool(base_model) != bool(pretraining):
        raise ValueError('Base model and pretraining_type params must be both set or both unset!')

    fs = FS.for_classifier(config.data.dataset, config.data.repr,
                           base_model=base_model, pretraining=pretraining,
                           classification_type=config.classification_type)

    fs.create_path_to_model(config.data, config.training_config)
    attach_dataset_aware_handlers_to_loggers(fs.path_to_model, 'main.log')

    print_gpu_info()

    text_field = fs.load_text_field()

    rnn_learner = create_nn_architecture(fs, text_field, LEVEL_LABEL,
                                         config.data,
                                         config.arch,
                                         config.min_log_coverage_percent)
    logger.info(rnn_learner)

    same_model_exists = fs.best_model_exists(rnn_learner)
    if same_model_exists and not force_rerun:
        logger.info(f'Model {fs.path_to_classification_model} already trained. Not rerunning training.'
                    f'To retrain the model with this parameters, specify --force-rerun flag')
        return
    elif same_model_exists:
        logger.info(f"Model {fs.path_to_classification_model} already trained. Forcing rerun.")

    if pretraining == PretrainingType.FULL:
        try:
            logger.info(f'Trying to load base classifier: {base_model}')
            fs.load_base_model(rnn_learner)
            logger.info('Base classifier model is loaded.')
        except Exception as e:
            logger.warning(e)
            logger.warning('Base classifier model not loaded. Training from scratch')

    elif pretraining == PretrainingType.ONLY_ENCODER:
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

    config_manager.save_config(config.training_config, fs.path_to_model)

    train(fs, rnn_learner, config.training, config.metrics)

    model = rnn_learner.model

    to_test_mode(model)
    sample_test_runs_file = os.path.join(fs.path_to_model, 'test_runs.out')
    n_predicitions = 6 if config.classification_type == 'level' else 2
    show_tests(fs.test_path, model, text_field, sample_test_runs_file,
               config.data.backwards, n_predicitions, config.testing.n_samples)
    logger.info("Classifier training finished successfully.")

    # plotting confusion matrix
    # preds = np.argmax(probs, axis=1)
    # probs = probs[:,1]
    # from sklearn.metrics import confusion_matrix
    # cm = confusion_matrix(y, preds)
    # plot_confusion_matrix(cm, data.classes)


def run(force_rerun: bool, params_path: Optional[str], changed_params_path: Optional[str],
        device_id: Optional[int]) -> None:
    module = get_params_module(params_path, 'cl_default_config')
    config = module.classifier_config
    if changed_params_path:
        with open(changed_params_path, 'r') as f:
            patch = dict(jsons.loads(f.read()))
            config = patch_config(config, patch)
    if gpu.gpu_available():
        gpu_id_to_use = device_id if device_id is not None else get_current_device()
        logger.debug(f'Using gpu with id: {gpu_id_to_use}')
        with device(gpu_id_to_use):
            run_on_device(config, force_rerun)
    else:
        run_on_device(config, force_rerun)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--force-rerun', action='store_const', const=True, default=False)
    parser.add_argument('--params-path', action='store', help='TODO')
    parser.add_argument('--changed-params-path', action='store', help='TODO')
    parser.add_argument('--device', action='store', type=int, help='TODO')
    args = parser.parse_args()
    run(args.force_rerun, args.params_path, args.changed_params_path, args.device)
