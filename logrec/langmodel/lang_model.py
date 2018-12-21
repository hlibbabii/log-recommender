import importlib
import json
from argparse import ArgumentParser
from enum import Enum
from shutil import copyfile
from time import time

import matplotlib

from fastai.model import validate
from logrec.dataprep import TRAIN_DIR, TEST_DIR, VALID_DIR, TEXT_FIELD_FILE, MODELS_DIR
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser, PreprocessingParam
from logrec.langmodel.config_manager import find_name_for_new_config, find_most_similar_config, PARAM_FILE_NAME
from logrec.langmodel.fullwordfinder import get_curr_seq, get_curr_seq_new, get_subword
from logrec.util.io_utils import file_mapper
from logrec.util.percent_chunks import normalize_percent_data, get_chunk_prefix

matplotlib.use('Agg')

from logrec.langmodel.utils import to_test_mode, gen_text, beautify_text, back_to_train_mode, \
    attach_dataset_aware_handlers_to_loggers
from logrec.util import io_utils


import logging
import os

import pandas

import torch
from functools import partial

import dill as pickle

from fastai.core import USE_GPU, Variable, to_np, np, V, no_grad_context, VV
from fastai.nlp import LanguageModelData, seq2seq_reg
from fastai import metrics
from torchtext import data

# for some reason this import should go here to avoid error

LEVEL_LABEL = data.Field(sequential=False)
logger = logging.getLogger(__name__)

N_CHUNKS = 1000

class Mode(Enum):
    TRAINING = "training"
    LEARNING_RATE_FINDING = "learning_rate_finding"


def include_to_df(filename, percent, start_from):
    basename = os.path.basename(filename)
    if basename.startswith("_"):
        return False
    chunk = float(get_chunk_prefix(basename))
    return start_from <= chunk < percent * N_CHUNKS * 0.01


def include_to_df_tester(percent, start_from):
    def tmp(filename):
        return 1 if include_to_df(filename, percent, start_from) else 0

    return tmp


def create_df_creator(percent, start_from):
    def tmp(dir):
        return create_df(dir, percent, start_from)

    return tmp


def create_df(dir, percent, start_from):
    lines = []
    files_total = sum(f for f in file_mapper(dir, include_to_df_tester(percent, start_from),
                                             extension=None, ignore_prefix="_"))

    cur_file = 0
    for root, dirs, files in os.walk(dir):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                if include_to_df(file, percent, start_from):
                    cur_file += 1
                    logger.info(f'Adding {os.path.join(root, file)} to dataframe [{cur_file} out of {files_total}]')
                    lines.extend([line for line in f])
    if not lines:
        raise ValueError(f"No data available: {os.path.abspath(dir)}")
    return pandas.DataFrame(lines)


def get_model(model_name, nn_arch, percent, start_from):
    dataset_name = params.nn_params["dataset_name"]
    path_to_dataset = os.path.join(params.nn_params["path_to_data"], dataset_name)
    path_to_model = os.path.join(path_to_dataset, model_name)

    train_df_path = os.path.join(path_to_dataset, TRAIN_DIR)
    train_df= create_df(train_df_path, percent, start_from)

    test_df_path = os.path.join(path_to_dataset, TEST_DIR)
    test_df = create_df(test_df_path, percent, start_from)

    valid_df_path = os.path.join(path_to_dataset, VALID_DIR)
    if not os.path.exists(valid_df_path):
        valid_df_path = test_df_path
    valid_df = create_df(valid_df_path, percent, start_from)

    text_field = data.Field()
    languageModelData = LanguageModelData.from_dataframes(path_to_model,
                                                          text_field, 0,
                                                          train_df, valid_df, test_df,
                                                          bs=nn_arch["bs"], validation_bs=params.nn_params["validation_bs"],
                                                          bptt=nn_arch["bptt"],
                                                          min_freq=nn_arch["min_freq"]
                                                          # not important since we remove rare tokens during preprocessing
                                                          )

    opt_fn = partial(torch.optim.Adam, betas=nn_arch['betas'])

    rnn_learner = languageModelData.get_model(opt_fn, nn_arch['em_sz'], nn_arch['nh'], nn_arch['nl'],
                                              dropouti=nn_arch['drop']['outi'],
                                              dropout=nn_arch['drop']['out'],
                                              wdrop=nn_arch['drop']['w'],
                                              dropoute=nn_arch['drop']['oute'],
                                              dropouth=nn_arch['drop']['outh'],
                                              text_field=text_field)
    rnn_learner.reg_fn = partial(seq2seq_reg, alpha=nn_arch['reg_fn']['alpha'], beta=nn_arch['reg_fn']['beta'])
    rnn_learner.clip = nn_arch['clip']

    logger.info(rnn_learner)

    try:
        rnn_learner.load(f'{params.nn_params["dataset_name"]}_best')
        model_trained = True
        # calculate_and_display_metrics(rnn_learner, nn_params['metrics'], text_field.vocab)
    except FileNotFoundError:
        logger.info(f"Model {os.path.join(dataset_name, model_name)} not found")
        model_trained = False
        try:
            rnn_learner.load(f'{params.nn_params["dataset_name"]}_best_base')
            logger.info("Base model detected and loaded")
        except FileNotFoundError:
            pass

    return rnn_learner, text_field, model_trained


def run_and_display_tests(m, text_field, nn_arch, nn_testing, path_to_save=None):
    to_test_mode(m)

    text = gen_text(m, text_field, nn_testing["starting_words"], nn_testing["how_many_words"])

    beautified_text = beautify_text(text)
    if path_to_save:
        logger.info(f"Generating sample text to {path_to_save}")
        with open(path_to_save, 'w') as f:
            f.write(beautified_text)
    else:
        logger.info("==============    SAMPLE TEXT    ========================")
        logger.info(beautified_text)

    back_to_train_mode(m, nn_arch['bs'])


def printGPUInfo():
    logger.info("Using GPU: " + str(USE_GPU))
    if USE_GPU:
        logger.info("Number of GPUs available: " + str(torch.cuda.device_count()))


def get_model_name_by_params(percent, start_from, path_to_dataset, nn_arch):
    normalized_percent, normalized_start_from = normalize_percent_data(percent, start_from)
    percent_prefix = f"{normalized_percent}_{'' if normalized_start_from == '0' else (normalized_start_from + '_')}"
    most_similar_model_name, config_diff = find_most_similar_config(percent_prefix, path_to_dataset, nn_arch)
    if config_diff == {}:
        return most_similar_model_name
    else: #nn wasn't run with this config yet
        name = find_name_for_new_config(percent_prefix,
                                        config_diff) if most_similar_model_name is not None else f"{percent_prefix}baseline"
        path_to_model = os.path.join(path_to_dataset, name)
        while os.path.exists(path_to_model):
            name = name + "_"
            path_to_model = os.path.join(path_to_dataset, name)
        return name

def find_and_plot_lr(rnn_learner, path_to_model):
    logger.info("Looking for the best learning rate...")
    # TODO we shouldnt pass file argument, when looking
    # for learning rate we should log to console
    rnn_learner.lr_find(file=open(os.path.join(path_to_model, 'training.log'), 'w'))

    dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(dir, path_to_model, 'lr_finder_plot.png')
    rnn_learner.sched.plot(path)
    logger.info(f"Plot is saved to {path}")


def one_hot(idx, size, cuda=False):
    a = np.zeros((1, size), np.float32)
    a[0][idx] = 1
    v = Variable(torch.from_numpy(a))
    if cuda: v = v.cuda()
    return v


def validate_with_cache(get_full_word_func, stepper, dl, metrics, epoch, seq_first, validate_skip, text_field, theta=2,
                        lambdah=0.0, window=1000):
    logging.info(f"Using theta: {theta}, lambdah: {lambdah}")
    bptts, losses, res = [], [], []
    seq = []
    ps = []
    seqs_in_batch_list = []
    stepper.reset(False)
    with no_grad_context():
        next_word_history = None
        pointer_history = None
        for (*x, y) in iter(dl):
            # x - [Variable(x1,x2, ... xn)]
            # y - Variable(x2...,xn, xn+1)
            batch_size = x[0].size(1)
            if batch_size != 1:
                raise ValueError("For now only batch v  vfrsize 1 is supported for validation with cache")
            preds, raw_outputs, l, targets = stepper.evaluate_with_cache(VV(x), VV(y))
            # preds [bptt x vocab size] Variable
            # raw_outputs [Variables[bptt x batch size x layer size], ...] - list, size: number of layers
            # l - cross entropy Variable [batch size]
            # targets [bptt]
            ntokens = preds.size(1)
            rnn_out = raw_outputs[-1].squeeze(1)  # from last layer
            output_flat = preds.view(-1, ntokens)
            # Fill pointer history
            start_idx = len(next_word_history) if next_word_history is not None else 0
            next_word_history = torch.cat(
                [one_hot(t.data[0], ntokens) for t in targets]) if next_word_history is None else torch.cat(
                [next_word_history, torch.cat([one_hot(t.data[0], ntokens) for t in targets])])
            # print(next_word_history)
            pointer_history = Variable(rnn_out.data) if pointer_history is None else torch.cat(
                [pointer_history, Variable(rnn_out.data)], dim=0)

            loss = 0
            seqs_in_batch = 0
            softmax_output_flat = torch.nn.functional.softmax(output_flat)
            bptts.append(softmax_output_flat.size(0))
            preds_with_cache = []
            for idx, vocab_loss in enumerate(softmax_output_flat):
                p = vocab_loss
                if start_idx + idx > window:
                    valid_next_word = next_word_history[start_idx + idx - window:start_idx + idx]
                    valid_pointer_history = pointer_history[start_idx + idx - window:start_idx + idx]
                    logits = torch.mv(valid_pointer_history, rnn_out[idx])
                    ptr_attn = torch.nn.functional.softmax(theta * logits).view(-1, 1)
                    ptr_dist = (ptr_attn.expand_as(valid_next_word) * valid_next_word).sum(0).squeeze()
                    p = lambdah * ptr_dist + (1 - lambdah) * vocab_loss
                    index = targets[idx].data[0]
                    # logging.info(f"========================================")
                    # logging.info(f"Actual word: {text_field.vocab.itos[index]}")
                    # logging.info("Result:")
                    # vals, indices = torch.topk(p, 3)
                    # for c, i in zip(vals, indices):
                    #     logging.info(f"{text_field.vocab.itos[i.data[0]]} ({c.data[0]})")
                    # logging.info("From cache:")
                    # vals, indices = torch.topk(ptr_dist, 3)
                    # for c,i in zip(vals, indices):
                    #     logging.info(f"{text_field.vocab.itos[i.data[0]]} ({c.data[0]})")
                    # logging.info("From nn:")
                    # vals, indices = torch.topk(vocab_loss, 3)
                    # for c,i in zip(vals, indices):
                    #     logging.info(f"{text_field.vocab.itos[i.data[0]]} ({c.data[0]})")
                ###
                current_target = targets[idx].data
                current_p = p[current_target]
                curr_seq, current_ps, seq, ps = get_full_word_func(seq, ps, current_target, current_p, text_field)
                if curr_seq is not None:
                    for pp in current_ps:
                        loss += (-torch.log(pp)).data[0]
                    seqs_in_batch += 1
                    if len(current_ps) > 0:
                        logger.info(" ".join(map(lambda x: text_field.vocab.itos[x[0]], curr_seq)))
                        lss = list(map(lambda x: (-torch.log(x)).data[0], current_ps))
                        logger.info("" + str(list(map(lambda x: f'{x:.3f}', lss))) + f'= {sum(lss):.3f}')
                        logger.info("============================")
                preds_with_cache.append(p)
            ###
            # hidden = repackage_hidden(hidden)
            next_word_history = next_word_history[-window:]
            pointer_history = pointer_history[-window:]
            res.append([f(torch.stack(preds_with_cache).data, y) for f in metrics])

            if seqs_in_batch > 0:
                loss = loss / seqs_in_batch
                losses.append(to_np(V(loss)))

                seqs_in_batch_list.append(seqs_in_batch)

        for pp in ps:
            loss += (-torch.log(pp)).data[0]
        losses.append(to_np(V(loss)))
        seqs_in_batch_list.append(1)

    return [np.average(losses, 0, weights=seqs_in_batch_list)] + list(np.average(np.stack(res), 0, weights=bptts))


def train_model(rnn_learner, path_to_dataset, dataset_name, model_name, nn_arch, lr):
    path_to_model = os.path.abspath(os.path.join(path_to_dataset, model_name))
    split_repr = PrepParamsParser.from_encoded_string(dataset_name)[PreprocessingParam.NO_SEP]
    if nn_arch['cycle']['n'] > 0:
        get_full_word_func = get_curr_seq if split_repr == 0 else get_curr_seq_new
        training_start_time = time()
        training_log_file = os.path.join(path_to_model, 'training.log')
        logger.info(f"Starting training, check {training_log_file} for training progress")
        vals, ep_vals = rnn_learner.fit(lr, n_cycle=nn_arch['cycle']['n'], wds=nn_arch['wds'],
                                        cycle_len=nn_arch['cycle']['len'], cycle_mult=nn_arch['cycle']['mult'],
                                        metrics=list(map(lambda x: getattr(metrics, x), nn_arch['training_metrics'])),
                                        cycle_save_name=dataset_name, get_ep_vals=True,
                                        best_save_name=f'{dataset_name}_best', file=f"{path_to_model}/training.log",
                                        valid_func=partial(validate_with_cache, get_full_word_func)
                                        )
        training_time_mins = int(time() - training_start_time) // 60
        with open(os.path.join(path_to_model, 'results.out'), 'w') as f:
            f.write(str(training_time_mins) + "\n")
            for _, vals in ep_vals.items():
                f.write(" ".join(map(lambda x: str(x), vals)) + "\n")
    else:
        logger.info("Number of epochs specified is 0. Not training...")
        rnn_learner.save(f'{dataset_name}_best')

    logger.info(f'Saving model: {path_to_model}')
    rnn_learner.save(dataset_name)
    rnn_learner.save_encoder(dataset_name + "_encoder")


def get_non_existent_model_name(path_to_dataset, base_model_name):
    model_name = base_model_name + "_extratrained"
    while os.path.exists(os.path.join(path_to_dataset, model_name)):
        model_name = model_name + "_"
    return model_name


def save_vocab_data(text_field, path_to_dataset):
    ####  TODO no need to save vocab data if it's already there in metadata
    # if its not ther esave t metadata

    io_utils.dump_dict_into_2_columns(text_field.vocab.freqs, os.path.join(path_to_dataset, 'vocab_all.txt'))
    pickle.dump(text_field, open(os.path.join(path_to_dataset, TEXT_FIELD_FILE), 'wb'))

    vocab_size = len(text_field.vocab.itos)
    logger.info(f'Dictionary size is: {vocab_size}')
    with open(os.path.join(path_to_dataset, 'vocab_size'), 'w') as f:
        f.write("# This is automatically generated file! Do not edit!\n")
        f.write(str(vocab_size))

    ####


def run(params):
    logger.info(f"Using params: {params.nn_params}")

    nn_arch = params.nn_params['arch']
    nn_testing = params.nn_params['testing']

    path_to_dataset = os.path.abspath(os.path.join(params.nn_params["path_to_data"], params.nn_params["dataset_name"]))

    percent = float(params.nn_params['percent'])
    start_from = float(params.nn_params['start_from'])
    if "base_model" in params.nn_params:
        base_model_name = params.nn_params["base_model"]
        path_to_best_model = os.path.join(path_to_dataset, base_model_name, MODELS_DIR,
                                          f'{params.nn_params["dataset_name"]}_best.h5')
        logger.info(f"Using base model: {base_model_name}")
        model_name = get_non_existent_model_name(path_to_dataset, base_model_name)
        path_to_model = os.path.join(path_to_dataset, model_name)
        path_to_model_models = os.path.join(path_to_model, MODELS_DIR)
        os.makedirs(path_to_model_models)
        path_to_model_best_base = os.path.join(path_to_model_models, f'{params.nn_params["dataset_name"]}_best_base.h5')
        try:
            logger.info(f"Copying from {path_to_best_model} "
                        f"to {path_to_model_best_base}")
            copyfile(path_to_best_model, path_to_model_best_base)
        except IOError:
            logger.error("Error copying file!")
            exit(1)
    else:
        logger.info("Not using base model. Training coefficients from scratch...")

        model_name = get_model_name_by_params(percent, start_from,
                                              path_to_dataset, nn_arch)
        path_to_model = os.path.join(path_to_dataset, model_name)
    if not os.path.exists(path_to_model):
        os.mkdir(path_to_model)
    attach_dataset_aware_handlers_to_loggers(path_to_model, 'main.log')

    printGPUInfo()
    force_rerun = True
    md = params.nn_params['mode']
    logger.info(f"Mode: {md}")
    logger.info(f"Path to model: {path_to_model}")

    learner, text_field, model_trained = get_model(model_name, nn_arch, percent, start_from)

    save_vocab_data(text_field, path_to_dataset)

    if model_trained and not force_rerun:
        logger.info(f'Model {path_to_model} already trained. Not rerunning training.')
        return

    with open(os.path.join(path_to_model, PARAM_FILE_NAME), 'w') as f:
        json.dump(nn_arch, f)

    if params.nn_params['mode'] == Mode.LEARNING_RATE_FINDING.value:
        if model_trained:
            logger.info(f"Forcing lr-finder rerun")
        find_and_plot_lr(learner, f'{path_to_model}')
    elif params.nn_params['mode'] == Mode.TRAINING.value:
        if model_trained:
            logger.info(f"Forcing training rerun")
        train_model(learner, path_to_dataset, params.nn_params["dataset_name"], model_name, nn_arch,
                    params.nn_params['lr'])
        logger.info("Loading the best model")
        learner.load(f'{params.nn_params["dataset_name"]}_best')
        m = learner.model
        gen_text_path = os.path.join(path_to_model, 'gen_text.out')
        run_and_display_tests(m, text_field, nn_arch, nn_testing, gen_text_path)
    else:
        raise AssertionError(f"Unknown mode: {params.nn_params['mode']}")



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    parser = ArgumentParser()
    parser.add_argument("params_file")
    args = parser.parse_args(['logrec.langmodel.params'])
    params = importlib.import_module(args.params_file)
    run(params)
