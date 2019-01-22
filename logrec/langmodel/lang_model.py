from argparse import ArgumentParser
from time import time
from typing import Union, Optional

import matplotlib
from torch.cuda import device
from torchtext.data import Field

from fastai.model import validate
from logrec.dataprep.preprocessors.model.placeholders import placeholders
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser, PreprocessingParam
from logrec.infrastructure import config_manager
from logrec.infrastructure.fractions_manager import create_df
from logrec.infrastructure.fs import FS, BEST_MODEL_NAME
from logrec.langmodel.cache import validate_with_cache
from logrec.langmodel.fullwordfinder import get_subword, get_curr_seq_new, get_curr_seq
from logrec.misc import attach_dataset_aware_handlers_to_loggers
from logrec.param.model import Data, Arch, LangmodelTraining, Testing, LangModelLrLearningParams, \
    LangModelTrainingParams
from logrec.util import gpu
from logrec.util.gpu import print_gpu_info, get_current_device
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
ENCODER_NAME = 'encoder'
LAST_MODEL_NAME = 'last'
LEVEL_LABEL = data.Field(sequential=False)
logger = logging.getLogger(__name__)


def create_nn_architecture(fs: FS, data: Data, arch: Arch, validation_bs: int, backwards: bool,
                           path=None, preloaded_text_field: Field = None) -> RNN_Learner:
    train_df_path = fs.train_path
    train_df = create_df(train_df_path, data.percent, data.start_from, backwards)

    test_df_path = fs.test_path
    test_df = create_df(test_df_path, data.percent, data.start_from, backwards)

    valid_df_path = fs.valid_path
    if not os.path.exists(valid_df_path):
        valid_df_path = test_df_path
    valid_df = create_df(valid_df_path, data.percent, data.start_from, backwards)
    if not preloaded_text_field:
        text_field = Field(tokenize=lambda s: s.split(" "), pad_token=placeholders['pad_token'])
    else:
        text_field = preloaded_text_field
        logger.info(f'Using preloaded text field. Vocab size is {len(text_field.vocab)}')
    languageModelData = LanguageModelData.from_dataframes(fs.path_to_model if not path else path,
                                                          text_field, 0,
                                                          train_df, valid_df, test_df,
                                                          bs=arch.bs, validation_bs=validation_bs,
                                                          bptt=arch.bptt,
                                                          min_freq=arch.min_freq
                                                          # not important since we remove rare tokens during preprocessing
                                                          )
    return create_learner(languageModelData, arch, text_field)


def create_learner(lang_model_data: LanguageModelData, arch: Arch, text_field: Field) -> RNN_Learner:
    opt_fn = partial(torch.optim.Adam, betas=arch.betas)

    rnn_learner = lang_model_data.get_model(opt_fn, arch.em_sz, arch.nh, arch.nl,
                                            dropouti=arch.drop.outi,
                                            dropout=arch.drop.out,
                                            wdrop=arch.drop.w,
                                            dropoute=arch.drop.oute,
                                            dropouth=arch.drop.outh,
                                            text_field=text_field, bidir=arch.bidir)
    rnn_learner.reg_fn = partial(seq2seq_reg, alpha=arch.reg_fn.alpha, beta=arch.reg_fn.beta)
    rnn_learner.clip = arch.clip

    return rnn_learner


def get_best_available_model(fs: FS, data: Data, arch: Arch, validation_bs: int, backwards: bool):
    preloaded_text_filed = fs.load_text_field()
    rnn_learner = create_nn_architecture(fs, data, arch, validation_bs, backwards,
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


def run_and_display_tests(learner: RNN_Learner, arch: Arch, testing: Testing, path_to_save=None,
                          backwards: bool = False):
    to_test_mode(learner.model)
    prepared_input = testing.starting_words.rstrip("\n").split(" ")
    text = gen_text(learner, prepared_input, testing.how_many_words)
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


def train_and_save_model(rnn_learner: RNN_Learner, fs: FS, training: LangmodelTraining):
    split_repr = PrepParamsParser.from_encoded_string(fs.repr)[PreprocessingParam.NO_SEP]
    only_validation = False
    n = training.cycle.n
    if training.cycle.n == 0:
        logger.info("Number of epochs specified is 0. Not training...")
        fs.save_best(rnn_learner)
        only_validation = True
        n = 1

    get_full_word_func = get_curr_seq if split_repr == 0 else get_curr_seq_new
    training_start_time = time()
    training_log_file = os.path.join(fs.path_to_model, 'training.log')
    logger.info(f"Starting training, check {training_log_file} for training progress")
    vals, ep_vals = rnn_learner.fit(lrs=training.lr, n_cycle=n, wds=training.wds,
                                    cycle_len=training.cycle.len, cycle_mult=training.cycle.mult,
                                    metrics=list(map(lambda x: getattr(metrics, x), training.metrics)),
                                    cycle_save_name='', get_ep_vals=True,
                                    file=open(training_log_file, 'w'),
                                    best_save_name=BEST_MODEL_NAME,
                                    valid_func=validate, only_validation=only_validation
                                    )
    training_time_mins = int(time() - training_start_time) // 60
    with open(os.path.join(fs.path_to_model, 'results.out'), 'w') as f:
        f.write(str(training_time_mins) + "\n")
        for _, vals in ep_vals.items():
            f.write(" ".join(map(lambda x: str(x), vals)) + "\n")

    rnn_learner.save(LAST_MODEL_NAME)
    rnn_learner.save_encoder(ENCODER_NAME)


def run_on_device(params: Union[LangModelLrLearningParams, LangModelTrainingParams],
                  find_lr: bool, force_rerun: bool) -> None:
    fs = FS.for_lang_model(params.data.dataset, params.data.repr, params.base_model)

    fs.create_path_to_model(params.data, params.langmodel_training_config)
    attach_dataset_aware_handlers_to_loggers(fs.path_to_model, 'main.log')

    print_gpu_info()

    learner, model_trained = get_best_available_model(fs, params.data, params.arch, params.validation_bs,
                                                      params.langmodel_training.backwards)

    fs.save_vocab_data(learner.text_field, params.data.percent, params.data.start_from)

    if model_trained and not force_rerun:
        logger.info(f'Model {fs.path_to_model} already trained. Not rerunning training.')
        return
    elif model_trained:
        logger.info(f"Forcing rerun")
    else:
        logger.info(f'Model with the same training config was not found.')

    config_manager.save_config(params.langmodel_training_config, fs.path_to_model)

    if find_lr:
        find_and_plot_lr(learner, fs)
    else:
        train_and_save_model(learner, fs, params.langmodel_training)
        model_loaded = fs.load_best(learner)
        if not model_loaded:
            raise AssertionError("The best model should have been trained and saved!")
        gen_text_path = os.path.join(fs.path_to_model, 'gen_text.out')
        run_and_display_tests(learner, params.arch, params.testing, gen_text_path, params.langmodel_training.backwards)


def run(find_lr: bool, force_rerun: bool, params_path: Optional[str], device_id: Optional[int]) -> None:
    module = get_params_module(params_path)
    params = module.langmodel_lr_learning_params if find_lr else module.langmodel_training_params
    if gpu.gpu_available():
        gpu_id_to_use = device_id if device_id is not None else get_current_device()
        with device(gpu_id_to_use):
            run_on_device(params, find_lr, force_rerun)
    else:
        run_on_device(params, find_lr, force_rerun)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--find-lr', action='store_const', const=True, default=False)
    parser.add_argument('--force-rerun', action='store_const', const=True, default=False)
    parser.add_argument('--params-path', action='store', help='TODO')
    parser.add_argument('--device', action='store', type=int, help='TODO')
    args = parser.parse_args()
    run(args.find_lr, args.force_rerun, args.params_path, args.device)
