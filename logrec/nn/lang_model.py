import importlib
import json
from argparse import ArgumentParser
from collections import defaultdict
from enum import Enum
from shutil import copyfile
from time import time

import deepdiff
import matplotlib

matplotlib.use('Agg')

import logging
import os

import pandas

import torch
from functools import partial

import dill as pickle

from fastai.core import USE_GPU
from fastai.nlp import LanguageModelData, seq2seq_reg
from fastai import metrics
from torchtext import data
from nn.utils import to_test_mode, back_to_train_mode, beautify_text, gen_text

# for some reason this import should go here to avoid error

logging.basicConfig(level=logging.DEBUG)

LEVEL_LABEL = data.Field(sequential=False)

class Mode(Enum):
    TRAINING = "training"
    LEARNING_RATE_FINDING = "learning_rate_finding"
    VOCAB_BUILDING = "vocab_building"


def create_df(dir):
    lines = []
    files_total = 0
    for root, dirs, files in os.walk(dir):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                if not file.startswith("_"):
                    files_total += 1

    DATAFRAME_LINES_THRESHOLD = 10 * 3
    cur_file = 0
    at_least_one_frame_created = False
    for root, dirs, files in os.walk(dir):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                if not file.startswith("_"):
                    cur_file += 1
                    logging.info(f'Adding {os.path.join(root, file)} to dataframe [{cur_file} out of {files_total}]')
                    lines.extend([line for line in f])
                    if len(lines) > DATAFRAME_LINES_THRESHOLD:
                        yield pandas.DataFrame(lines)
                        lines = []
                        at_least_one_frame_created = True

    if lines:
        yield pandas.DataFrame(lines)
        at_least_one_frame_created = True
    if not at_least_one_frame_created:
        raise ValueError(f"No data available: {os.path.abspath(dir)}")


def get_model(model_name, only_build_vocab=False):
    dataset_name = params.nn_params["dataset_name"]
    path_to_dataset = f'{params.nn_params["path_to_data"]}/{dataset_name}'
    path_to_model = f'{path_to_dataset}/{model_name}'

    train_df_path = f'{path_to_dataset}/train/'
    test_df_path =  f'{path_to_dataset}/test/'
    valid_df_path = f'{path_to_dataset}/valid/'
    if not os.path.exists(valid_df_path):
        valid_df_path = test_df_path

    text_field = data.Field()
    languageModelData = LanguageModelData.from_dataframes(path_to_model,
                                                          text_field, 0, create_df,
                                                          train_df_path, valid_df_path, test_df_path,
                                                          bs=nn_arch["bs"], validation_bs=params.nn_params["validation_bs"],
                                                          bptt=nn_arch["bptt"],
                                                          min_freq=nn_arch["min_freq"],
                                                          only_build_vocab=only_build_vocab
                                                          # not important since we remove rare tokens during preprocessing
                                                          )
    with open(f'{path_to_dataset}/vocab_all.txt', 'w') as f:
        for word, freq in text_field.vocab.freqs.items():
            f.write(f'{str(word)} {str(freq)}\n')
    pickle.dump(text_field, open(f'{path_to_dataset}/TEXT.pkl', 'wb'))

    vocab_size=len(text_field.vocab.itos)
    logging.info(f'Dictionary size is: {vocab_size}')
    with open(f'{path_to_dataset}/vocab_size', 'w') as f:
        f.write("# This is automatically generated file! Do not edit!\n")
        f.write(str(vocab_size))
    if only_build_vocab:
        return None, text_field, None

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

    logging.info(rnn_learner)

    try:
        rnn_learner.load(f'{params.nn_params["dataset_name"]}_best')
        model_trained = True
        # calculate_and_display_metrics(rnn_learner, nn_params['metrics'], text_field.vocab)
    except FileNotFoundError:
        logging.warning(f"Model {dataset_name}/{model_name} not found")
        model_trained = False
        try:
            rnn_learner.load(f'{params.nn_params["dataset_name"]}_best_base')
            logging.info("Base model detected and loaded")
        except FileNotFoundError:
            pass

    return rnn_learner, text_field, model_trained

def run_and_display_tests(m, text_field, path_to_save=None):
    to_test_mode(m)
    print("==============        TESTS       ====================")

    text = gen_text(m, text_field, nn_testing["starting_words"], nn_testing["how_many_words"])

    beautified_text = beautify_text(text)
    print(beautified_text)
    if path_to_save:
        with open(path_to_save, 'w') as f:
            f.write(beautified_text)

    back_to_train_mode(m, nn_arch['bs'])

PARAM_FILE_NAME = 'params.json'
DEEPDIFF_ADDED = 'dictionary_item_added'
DEEPDIFF_REMOVED = 'dictionary_item_removed'
DEEPDIFF_CHANGED = 'values_changed'

def find_most_similar_config(path_to_dataset, current_config):
    config_dict = defaultdict(list)
    for (dirpath, dirnames, filenames) in os.walk(path_to_dataset):
        for dirname in dirnames:
            file_path = os.path.join(dirpath, dirname, PARAM_FILE_NAME)
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    config = json.load(f)
                dd = deepdiff.DeepDiff(config, current_config)
                if dd == {}:
                    return dirname, {}
                else:
                    n_changed_params=(len(dd[DEEPDIFF_ADDED]) if DEEPDIFF_ADDED in dd else 0) \
                                     + (len(dd[DEEPDIFF_CHANGED]) if DEEPDIFF_CHANGED in dd else 0) \
                                     + (len(dd[DEEPDIFF_REMOVED]) if DEEPDIFF_REMOVED in dd else 0)
                    config_dict[n_changed_params].append((dirname, dd))
    if not config_dict:
        return None, deepdiff.DeepDiff({}, current_config)
    else:
        return config_dict[min(config_dict)][-1]

def extract_last_key(keys):
    last_apostrophe = keys.rindex('\'')
    return keys[keys[:last_apostrophe].rindex('\'') + 1:last_apostrophe]


def find_name_for_new_config(config_diff):
    name = ""
    if DEEPDIFF_CHANGED in config_diff:
        for key, val in config_diff[DEEPDIFF_CHANGED].items():
            name += extract_last_key(key)
            name += "_"
            name += str(val['new_value'])
            name += "_"
    if DEEPDIFF_ADDED in config_diff:
        for key in config_diff[DEEPDIFF_ADDED]:
            name += extract_last_key(key)
            name += "_"
    if DEEPDIFF_REMOVED in config_diff:
        for key in config_diff[DEEPDIFF_REMOVED]:
            name += extract_last_key(key)
            name += "_"
    if name:
        name = name[:-1]
    return name


def printGPUInfo():
    logging.info("Using GPU: " + str(USE_GPU))
    if USE_GPU:
        logging.info("Number of GPUs available: " + str(torch.cuda.device_count()))


def get_model_name_by_params():
    folder, config_diff = find_most_similar_config(path_to_dataset, nn_arch)
    if config_diff == {}:
        return folder
    else: #nn wasn't run with this config yet
        name = find_name_for_new_config(config_diff) if folder is not None else "baseline"
        path_to_model = f'{path_to_dataset}/{name}'
        while os.path.exists(path_to_model):
            name = name + "_"
            path_to_model = f'{path_to_dataset}/{name}'
        return name

def find_and_plot_lr(rnn_learner, path_to_model):
    logging.info("Looking for the best learning rate...")
    rnn_learner.lr_find()

    dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(dir, path_to_model, 'lr_finder_plot.png')
    rnn_learner.sched.plot(path)
    logging.info(f"Plot is saved to {path}")


def train_model(rnn_learner, path_to_dataset, model_name):
    dataset_name = params.nn_params["dataset_name"]
    training_start_time = time()
    vals, ep_vals = rnn_learner.fit(params.nn_params['lr'], n_cycle=nn_arch['cycle']['n'], wds=nn_arch['wds'],
                                    cycle_len=nn_arch['cycle']['len'], cycle_mult=nn_arch['cycle']['mult'],
                                    metrics=list(map(lambda x: getattr(metrics, x), nn_arch['training_metrics'])),
                                    cycle_save_name=dataset_name, get_ep_vals=True, best_save_name=f'{dataset_name}_best')
    training_time_mins = int(time() - training_start_time) // 60
    with open(f'{path_to_dataset}/{model_name}/results.out', 'w') as f:
        f.write(str(training_time_mins) + "\n")
        for _, vals in ep_vals.items():
            f.write(" ".join(map(lambda x: str(x), vals)) + "\n")

    logging.info(f'Saving model: {dataset_name}/{model_name}')
    rnn_learner.save(dataset_name)
    rnn_learner.save_encoder(dataset_name + "_encoder")


if __name__ =='__main__':
    parser = ArgumentParser()
    parser.add_argument("params_file")
    args = parser.parse_args()
    params = importlib.import_module(args.params_file)
    logging.info(f"Using params: {params.nn_params}")

    nn_arch = params.nn_params['arch']
    nn_testing = params.nn_params['testing']

    printGPUInfo()
    logging.info("Using the following parameters:")
    logging.info(nn_arch)

    path_to_dataset = f'{params.nn_params["path_to_data"]}/{params.nn_params["dataset_name"]}'
    force_rerun = False
    md=params.nn_params['mode']
    logging.info(f"Mode: {md}")
    if md == Mode.VOCAB_BUILDING.value:
        logging.info("Vocab building mode.")
        learner, text_field, model_trained = get_model("vocab", only_build_vocab=True)
        logging.info("Vocab is built.")
        exit(0)

    if "base_model" in params.nn_params:
        base_model_name = params.nn_params["base_model"]
        path_to_best_model = f'{path_to_dataset}/{base_model_name}/models/{params.nn_params["dataset_name"]}_best.h5'
        logging.info(f"Using base model: {base_model_name}")
        model_name = base_model_name  + "_extratrained"
        path_to_model = f'{path_to_dataset}/{model_name}'
        while os.path.exists(path_to_model):
            model_name = model_name + "_"
            path_to_model = f'{path_to_dataset}/{model_name}'
        os.mkdir(path_to_model)
        path_to_model_models = f'{path_to_model}/models'
        os.mkdir(path_to_model_models)
        path_to_model_best_base = f'{path_to_model_models}/{params.nn_params["dataset_name"]}_best_base.h5'
        try:
            logging.info(f"Copying from {os.path.abspath(path_to_best_model)} "
                         f"to {os.path.abspath(path_to_model_best_base)}")
            copyfile(path_to_best_model, path_to_model_best_base)
        except IOError:
            logging.error("Error copying file!")
            exit(1)
    else:
        logging.info("Not using base model. Training coefficients from scratch...")
        model_name = get_model_name_by_params()
        path_to_model = f'{path_to_dataset}/{model_name}'

    logging.info(f"Path to model: {os.path.abspath(path_to_model)}")
    if not os.path.exists(path_to_model):
        os.mkdir(path_to_model)

    learner, text_field, model_trained = get_model(model_name)
    vocab_file = f'{path_to_dataset}/TEXT.pkl'
    if not os.path.exists(vocab_file):
        with open(vocab_file, 'w') as f:
            f.dump(text_field)
    rerunning_model = model_trained
    if not rerunning_model or force_rerun:
        with open(f'{path_to_model}/{PARAM_FILE_NAME}', 'w') as f:
            json.dump(nn_arch, f)
        # with open(f'{path_to_dataset}/{name}/config_diff.json', 'w') as f:
        #     json.dump(config_diff, f)

        if params.nn_params['mode'] == Mode.LEARNING_RATE_FINDING.value:
            if rerunning_model:
                logging.info(f"Forcing lr-finder rerun")
            find_and_plot_lr(learner, f'{path_to_model}')
        elif params.nn_params['mode'] == Mode.TRAINING.value:
            if rerunning_model:
                logging.info(f"Forcing training rerun")
            train_model(learner, path_to_dataset, model_name)
            logging.info("Loading the best model")
            learner.load(f'{params.nn_params["dataset_name"]}_best')
            m = learner.model
            run_and_display_tests(m, text_field, f'{path_to_model}/gen_text.out')
        else:
            raise AssertionError("Unknown mode")
    else:
        logging.info(f'Model {params.nn_params["dataset_name"]}/{model_name} already trained. Not rerunning training.')
