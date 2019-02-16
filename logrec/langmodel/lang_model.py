from argparse import ArgumentParser
from time import time
from typing import Union, Optional, List

import jsons
import matplotlib
from torch.cuda import device
from torchtext.data import Field

from fastai.model import validate
from logrec.config.patch import patch_config
from logrec.dataprep.model.placeholders import placeholders
from logrec.dataprep.prepconfig import PrepParam, PrepConfig
from logrec.features.early_stop import EarlyStopping
from logrec.infrastructure import config_manager
from logrec.infrastructure.fractions_manager import create_df_gen
from logrec.infrastructure.fs import FS, BEST_MODEL_NAME, BEST_LOSS_FILENAME, BEST_ACC_FILENAME, BEST_EPOCH_FILENAME, \
    ENCODER_NAME
from logrec.langmodel.validation import custom_validate
from logrec.misc import attach_dataset_aware_handlers_to_loggers
from logrec.config.model import Data, Arch, LMTraining, LMTesting, LMLRConfig, LMConfig, Cache
from logrec.util import gpu
from logrec.util.gpu import print_gpu_info, get_current_device
from logrec.util.profiler import print_prof_data
from logrec.util.util import get_params_module

matplotlib.use('Agg')

from logrec.modeltest import to_test_mode, gen_text, beautify_text, back_to_train_mode

import logging
import os

import torch
from functools import partial


from fastai import metrics
from fastai.nlp import LanguageModelData, seq2seq_reg, RNN_Learner, SequentialRNN
from torchtext import data

# for some reason this import should go here to avoid error
LEVEL_LABEL = data.Field(sequential=False)
logger = logging.getLogger(__name__)


def create_nn_architecture(fs: FS, data: Data, arch: Arch,
                           path=None, preloaded_text_field: Field = None) -> RNN_Learner:
    train_df_path = fs.train_path
    train_df_gen = create_df_gen(train_df_path, data.percent, data.start_from, data.backwards)

    test_df_path = fs.test_path
    test_df_gen = create_df_gen(test_df_path, data.percent, data.start_from, data.backwards)

    valid_df_path = fs.valid_path
    if not os.path.exists(valid_df_path):
        valid_df_path = test_df_path
    valid_df_gen = create_df_gen(valid_df_path, data.percent, data.start_from, data.backwards)
    if not preloaded_text_field:
        text_field = Field(tokenize=lambda s: s.split(" "), pad_token=placeholders['pad_token'])
    else:
        text_field = preloaded_text_field
        logger.info(f'Using preloaded text field. Vocab size is {len(text_field.vocab)}')
    languageModelData = LanguageModelData.from_dataframes(fs.path_to_model if not path else path,
                                                          text_field, 0,
                                                          train_df_gen, valid_df_gen, test_df_gen,
                                                          bs=arch.bs, validation_bs=arch.validation_bs,
                                                          bptt=arch.bptt,
                                                          min_freq=0
                                                          # not important since we remove rare tokens during preprocessing
                                                          )
    return create_learner(languageModelData, arch, text_field)


def create_learner(lang_model_data: LanguageModelData, arch: Arch, text_field: Field) -> RNN_Learner:
    opt_fn = partial(torch.optim.Adam, betas=arch.adam_betas)

    dropout_multiplier = arch.drop.multiplier
    rnn_learner = lang_model_data.get_model(opt_fn, arch.em_sz, arch.nh, arch.nl,
                                            dropout=arch.drop.out * dropout_multiplier,
                                            dropouti=arch.drop.outi * dropout_multiplier,
                                            wdrop=arch.drop.w * dropout_multiplier,
                                            dropoute=arch.drop.oute * dropout_multiplier,
                                            dropouth=arch.drop.outh * dropout_multiplier,
                                            text_field=text_field, bidir=arch.bidir)
    rnn_learner.reg_fn = partial(seq2seq_reg, alpha=arch.reg_fn.alpha, beta=arch.reg_fn.beta)
    rnn_learner.clip = arch.clip

    return rnn_learner


def get_best_available_model(fs: FS, data: Data, arch: Arch):
    preloaded_text_filed = fs.load_text_field()
    rnn_learner = create_nn_architecture(fs, data, arch,
                                         path=None,
                                         preloaded_text_field=preloaded_text_filed)
    logger.info(rnn_learner)

    logger.info("Checking if there exists a model with the same architecture")
    model_loaded = fs.load_best(rnn_learner)
    if not model_loaded and fs.base_model_specified:
        logger.info(f'Trying to load base model: {fs.base_model_id}')
        try:
            fs.load_base_model(rnn_learner)
        except FileNotFoundError:
            logger.warning("Base model was not found. Training model from scratch")

    return rnn_learner, model_loaded


def run_and_display_tests(learner: RNN_Learner, arch: Arch, testing: LMTesting, backwards: bool, path_to_save=None):
    to_test_mode(learner.model)
    prepared_input = testing.starting_words.rstrip("\n").split(" ")
    text = gen_text(learner, prepared_input, testing.n_words_to_generate)
    if backwards:
        text.reverse()
    beautified_text = beautify_text(" ".join(text))
    if path_to_save:
        logger.info(f"Generating sample text to {path_to_save}")
        with open(path_to_save, 'w') as f:
            f.write(beautified_text)
    else:
        logger.info("==============    SAMPLE TEXT    ========================")
        logger.info(beautified_text)

    back_to_train_mode(learner.model, arch.bs)


def find_and_plot_lr(rnn_learner: RNN_Learner, fs: FS):
    logger.info("Looking for the best learning rate...")
    # TODO we shouldnt pass file argument, when looking
    # for learning rate we should log to console
    rnn_learner.lr_find(file=open(os.path.join(fs.path_to_model, 'training.log'), 'w'))

    rnn_learner.sched.plot(fs.path_to_lr_plot)
    logger.info(f"Plot is saved to {fs.path_to_lr_plot}")


def get_validation_function(cache: Cache, use_subword_aware_metrics, text_field: Field):
    if not cache and not use_subword_aware_metrics:
        return validate

    return partial(custom_validate, cache, text_field, use_subword_aware_metrics)


def train_and_save_model(rnn_learner: RNN_Learner, fs: FS, training: LMTraining, metric_list: List[str],
                         cache: Cache, use_subword_aware_metrics: bool):
    only_validation = False
    n = training.cycle.n
    if training.cycle.n == 0:
        logger.info("Number of epochs specified is 0. Not training...")
        fs.save_best(rnn_learner)
        only_validation = True
        n = 1

    training_start_time = time()
    training_log_file = os.path.join(fs.path_to_model, 'training.log')
    logger.info(f"Starting training, check {training_log_file} for training progress")
    callbacks = []

    if training.early_stop:
        callbacks.append(EarlyStopping(rnn_learner,
                                       save_path=BEST_MODEL_NAME,
                                       best_loss_path=BEST_LOSS_FILENAME,
                                       best_acc_path=BEST_ACC_FILENAME,
                                       best_epoch_path=BEST_EPOCH_FILENAME,
                                       enc_path=ENCODER_NAME))

    validation_function = get_validation_function(cache, use_subword_aware_metrics, rnn_learner.text_field)
    vals, ep_vals = rnn_learner.fit(lrs=training.lr, n_cycle=n, wds=training.wds,
                                    cycle_len=training.cycle.len, cycle_mult=training.cycle.mult,
                                    metrics=list(map(lambda x: getattr(metrics, x), metric_list)),
                                    get_ep_vals=True,
                                    file=open(training_log_file, 'w'),
                                    callbacks=callbacks,
                                    valid_func=validation_function, only_validation=only_validation
                                    )
    training_time_mins = int(time() - training_start_time) // 60
    with open(os.path.join(fs.path_to_model, 'results.out'), 'w') as f:
        f.write(str(training_time_mins) + "\n")
        for _, vals in ep_vals.items():
            f.write(" ".join(map(lambda x: str(x), vals)) + "\n")


def use_minibatches_for_validation(cache: Cache, subword_aware_metrics: bool):
    return not cache and not subword_aware_metrics


def run_on_device(config: Union[LMLRConfig, LMConfig],
                  find_lr: bool, force_rerun: bool) -> None:
    fs = FS.for_lang_model(config.data.dataset, config.data.repr, config.base_model)

    fs.create_path_to_model(config.data, config.training_config)
    attach_dataset_aware_handlers_to_loggers(fs.path_to_model, 'main.log')

    print_gpu_info()

    learner, model_trained = get_best_available_model(fs, config.data, config.arch)

    fs.save_vocab_data(learner.text_field, config.data.percent, config.data.start_from)

    if model_trained and not force_rerun:
        logger.info(f'Model {fs.path_to_model} already trained. Not rerunning training.')
        return
    elif model_trained:
        logger.info(f"Forcing rerun")
    else:
        logger.info(f'Model with the same training config was not found.')

    config_manager.save_config(config.training_config, fs.path_to_model)

    if find_lr:
        find_and_plot_lr(learner, fs)
    else:
        train_and_save_model(learner, fs, config.training, config.metrics, config.cache,
                             config.use_subword_aware_metrics)
        model_loaded = fs.load_best(learner)
        if not model_loaded:
            raise AssertionError("The best model should have been trained and saved!")
        gen_text_path = os.path.join(fs.path_to_model, 'gen_text.out')
        run_and_display_tests(learner, config.arch, config.testing, config.data.backwards, gen_text_path)


def run(find_lr: bool, force_rerun: bool, params_path: Optional[str], changed_params_path: Optional[str],
        device_id: Optional[int]) -> None:
    if find_lr:
        module = get_params_module(params_path, 'lm_lr_default_config')
        config = module.lm_lr_config
    else:
        module = get_params_module(params_path, 'lm_default_config')
        config = module.lm_config
    if changed_params_path:
        with open(changed_params_path, 'r') as f:
            patch = dict(jsons.loads(f.read()))
            config = patch_config(config, patch)
    logger.info(f'Using config: {jsons.dumps(config)}')
    if gpu.gpu_available():
        gpu_id_to_use = device_id if device_id is not None else get_current_device()
        with device(gpu_id_to_use):
            run_on_device(config, find_lr, force_rerun)
    else:
        run_on_device(config, find_lr, force_rerun)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--find-lr', action='store_const', const=True, default=False)
    parser.add_argument('--force-rerun', action='store_const', const=True, default=False)
    parser.add_argument('--params-path', action='store', help='TODO')
    parser.add_argument('--changed-params-path', action='store', help='TODO')
    parser.add_argument('--device', action='store', type=int, help='TODO')
    args = parser.parse_args()
    run(args.find_lr, args.force_rerun, args.params_path, args.changed_params_path,
        args.device)
    print_prof_data()
