import json
from collections import defaultdict
from time import time

import deepdiff
import matplotlib

from logrec.dataprep import TEST_DIR, TEXT_FIELD_FILE
from logrec.langmodel.utils import output_predictions, back_to_train_mode, to_test_mode

matplotlib.use('Agg')

from logrec.classifier.log_loc_dataset import LogLocationDataset
from logrec.classifier.classifier_params import params, Mode


import logging
import os

import pandas

import torch
from functools import partial

from fastai.core import USE_GPU
from fastai.nlp import seq2seq_reg, TextData
import dill as pickle
from fastai import metrics
from torchtext import data

logging.basicConfig(level=logging.DEBUG)

nn_arch = params['arch']
nn_testing = params['testing']


def create_df(dir):
    lines = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            with open(os.path.join(root, file), 'r') as f:
                lines.extend([line for line in f])
    if not lines:
        raise ValueError(f"No data available: {dir}")
    return pandas.DataFrame(lines)


arch = params['arch']

def get_model(model_name):
    dataset_name = params["dataset_name"]
    path_to_dataset = os.path.join(params["path_to_data"], dataset_name)
    path_to_model = os.path.join(path_to_dataset, model_name)

    vocab_file = os.path.join(path_to_dataset, TEXT_FIELD_FILE)
    if os.path.exists(vocab_file):
        text_field = pickle.load(open(vocab_file, 'rb'))
    else:
        raise FileNotFoundError(vocab_file)
    level_label = data.Field(sequential=False)
    splits = LogLocationDataset.splits(text_field, level_label, path=path_to_dataset)

    text_data = TextData.from_splits(path_to_model, splits, arch['bs'])
    # text_data.classes

    opt_fn = partial(torch.optim.Adam, betas=(0.7, 0.99))

    rnn_learner = text_data.get_model(opt_fn, 50, arch['bptt'], arch['em_sz'], arch['nh'], arch['nl'],
                                      dropouti=arch['drop']['outi'],
                                      dropout=arch['drop']['out'],
                                      wdrop=arch['drop']['w'],
                                      dropoute=arch['drop']['oute'],
                                      dropouth=arch['drop']['outh'])

    #reguarizing LSTM paper -- penalizing large activations -- reduce overfitting
    rnn_learner.reg_fn = partial(seq2seq_reg,
                                 alpha=arch['reg_fn']['alpha'],
                                 beta=arch['reg_fn']['beta'])

    # rnn_learner.lr_find()
    # rnn_learner.sched.plot()

    logging.info(f'Dictionary size is: {len(text_field.vocab.itos)}')
    logging.info(rnn_learner)

    try:
        rnn_learner.load(dataset_name)
        model_trained = True
        # calculate_and_display_metrics(rnn_learner, nn_params['metrics'], text_field.vocab)
    except FileNotFoundError:
        logging.warning(f"Model {os.path.join(dataset_name, model_name)} not found")
        model_trained = False

    return rnn_learner, text_field, level_label, model_trained

def run_and_display_tests(m, text_field, LEVEL_LABEL, path_to_save, path_to_dataset):
    to_test_mode(m)
    with open(path_to_save, 'w') as d:
        print("==============        TESTS -- TRUE      ====================")

        with open(os.path.join(path_to_dataset, TEST_DIR, 'true', 'context.0.src'), 'r') as f:
            counter = 0
            for line in f:
                if counter > 30:
                    break
                counter += 1
                print(f'{counter}\n')
                d.write(f'{counter}\n')
                predictions = output_predictions(m, text_field, LEVEL_LABEL, line, 3, path_to_save)
                print(predictions)
                d.write(predictions)

        print("==============        TESTS -- FALSE     ====================")

        with open(os.path.join(path_to_dataset, TEST_DIR, 'false', 'context.0.src'), 'r') as f:
            counter = 0
            for line in f:
                if counter > 30:
                    break
                counter += 1
                print(f'{counter}\n')
                d.write(f'{counter}\n')
                predictions = output_predictions(m, text_field, LEVEL_LABEL, line, 3, path_to_save)
                print(predictions)
                d.write(predictions)

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
        path_to_model = os.path.join(path_to_dataset, name)
        while os.path.exists(path_to_model):
            name = name + "_"
            path_to_model = os.path.join(path_to_dataset, name)
        return name

def find_and_plot_lr(rnn_learner, path_to_model):
    logging.info("Looking for the best learning rate...")
    rnn_learner.lr_find()

    dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(dir, path_to_model, 'lr_finder_plot.png')
    rnn_learner.sched.plot(path)
    logging.info(f"Plot is saved to {path}")


def train_model(rnn_learner, path_to_dataset, model_name):
    dataset_name = params["dataset_name"]
    training_start_time = time()
    vals, ep_vals = rnn_learner.fit(params['lr'], n_cycle=nn_arch['cycle']['n'], wds=nn_arch['wds'],
                                    cycle_len=nn_arch['cycle']['len'], cycle_mult=nn_arch['cycle']['mult'],
                                    metrics=list(map(lambda x: getattr(metrics, x), nn_arch['training_metrics'])),
                                    cycle_save_name=dataset_name, get_ep_vals=True)
    training_time_mins = int(time() - training_start_time) // 60
    with open(os.path.join(path_to_dataset, model_name, 'results.out'), 'w') as f:
        f.write(str(training_time_mins) + "\n")
        for _, vals in ep_vals.items():
            f.write(" ".join(map(lambda x: str(x), vals)) + "\n")

    logging.info(f'Saving model: {os.path.join(dataset_name, model_name)}')
    rnn_learner.save(dataset_name)
    rnn_learner.save_encoder(dataset_name + "_encoder")


if __name__ =='__main__':
    printGPUInfo()
    logging.info("Using the following parameters:")
    logging.info(nn_arch)
    path_to_dataset = os.path.join(params["path_to_data"], params["dataset_name"])
    force_rerun = True
    model_name = get_model_name_by_params()
    path_to_model = os.path.join(path_to_dataset, model_name)

    if not os.path.exists(path_to_model):
        os.mkdir(path_to_model)

    learner, text_field, level_field, model_trained = get_model(model_name)
    if not model_trained or force_rerun:
        with open(os.path.join(path_to_model, PARAM_FILE_NAME), 'w') as f:
            json.dump(nn_arch, f)
        # with open(f'{path_to_dataset}/{name}/config_diff.json', 'w') as f:
        #     json.dump(config_diff, f)

        if params['mode'] is Mode.LEARNING_RATE_FINDING:
            if model_trained:
                logging.info(f"Forcing lr-finder rerun")
            find_and_plot_lr(learner, os.path.join(path_to_dataset, model_name))
        elif params['mode'] is Mode.TRAINING:
            if model_trained:
                logging.info(f"Forcing training rerun")
            train_model(learner, path_to_dataset, model_name)
            m = learner.model
            run_and_display_tests(m, text_field, level_field, os.path.join(path_to_model, 'gen_text.out'),
                                  path_to_dataset)
        else:
            raise AssertionError("Unknown mode")
    else:
        logging.info(
            f'Model {os.path.join(nn_params["dataset_name"], model_name)} already trained. Not rerunning training.')
