import json
from collections import defaultdict
from time import time

import deepdiff
import matplotlib
matplotlib.use('Agg')

import logging
import os

import pandas

import torch
from functools import partial

from fastai.core import USE_GPU
from fastai.metrics import top_k, MRR
from fastai.nlp import LanguageModelData, seq2seq_reg
from params import Mode, nn_params
from utils import to_test_mode, gen_text, back_to_train_mode, beautify_text
import dill as pickle
from fastai import metrics
from torchtext import data

logging.basicConfig(level=logging.DEBUG)

nn_arch = nn_params['arch']
nn_testing = nn_params['testing']

def display_not_guessed_examples(examples, vocab):
    exs = []
    for input, num, preds, target in examples:
        exs.append((
            beautify_text(" ".join([vocab.itos[inp]
                                    if ind != num + 1 else "[[[" + vocab.itos[inp] + "]]]"
                                    for ind, inp in enumerate(input)])),
            num,
            [vocab.itos[p] for p in preds],
            vocab.itos[target]
    ))
    for ex in exs:
        logging.info(f'                    ... {ex[0]}')
        logging.info(f'                    ... {ex[1]}')
        logging.info(f'                    ... {ex[2]}')
        logging.info(f'                    ... {ex[3]}')
        logging.info(f'===============================================')


def calc_and_display_top_k(rnn_learner, metric, vocab):
    spl = metric.split("_")
    cat_index = spl.index("cat")
    if cat_index == -1 or len(spl) <= cat_index + 1:
        raise ValueError(f'Illegal metric format: {metric}')
    ks = list(map(lambda x: int(x), spl[1: cat_index]))
    cat = int(spl[cat_index + 1])

    accuracies, examples = top_k(*rnn_learner.predict_with_targs(True), ks, cat)

    logging.info(f'Current tops are ...')
    logging.info(f'                    ... {accuracies}')
    if spl[-1] == 'show':
        display_not_guessed_examples(examples, vocab)


def calculate_and_display_metrics(rnn_learner, metrics, vocab):
    for metric in metrics:
        if metric.startswith("topk"):
            calc_and_display_top_k(rnn_learner, metric, vocab)
        elif metric == 'mrr':
            mrr = MRR(*rnn_learner.predict_with_targs(True))
            logging.info(f"mrr: {mrr}")


def create_df(basic_path):
    counter = 0
    lines = []
    file = f'{basic_path}/contexts.{counter}.src'
    while os.path.exists(file):
        with open(file, 'r') as f:
            lines.extend([line for line in f])
        counter += 1
        file = f'{basic_path}/contexts.{counter}.src'
    if not lines:
        raise ValueError(f"No data available: {basic_path}")
    return pandas.DataFrame(lines)


def get_language_model(model_name, run_training=True):
    dataset_name = nn_params["dataset_name"]
    path_to_dataset = f'{nn_params["path_to_data"]}/{dataset_name}'
    path_to_model = f'{path_to_dataset}/{model_name}'

    train_df = create_df(f'{path_to_dataset}/train/')
    test_df = create_df(f'{path_to_dataset}/test/')

    text_field = data.Field()
    languageModelData = LanguageModelData.from_dataframes(path_to_model,
                                                          text_field, 0, train_df, test_df, test_df,
                                                          bs=nn_arch["bs"],
                                                          bptt=nn_arch["bptt"],
                                                          min_freq=nn_arch["min_freq"]
                                                          # not important since we remove rare tokens during preprocessing
                                                          )
    pickle.dump(text_field, open(f'{path_to_dataset}/TEXT.pkl', 'wb'))

    logging.info(f'Dictionary size is: {len(text_field.vocab.itos)}')

    opt_fn = partial(torch.optim.Adam, betas=nn_arch['betas'])

    rnn_learner = languageModelData.get_model(opt_fn, nn_arch['em_sz'], nn_arch['nh'], nn_arch['nl'],
                                              dropouti=nn_arch['drop']['outi'],
                                              dropout=nn_arch['drop']['out'],
                                              wdrop=nn_arch['drop']['w'],
                                              dropoute=nn_arch['drop']['oute'],
                                              dropouth=nn_arch['drop']['outh'])
    rnn_learner.reg_fn = partial(seq2seq_reg, alpha=nn_arch['reg_fn']['alpha'], beta=nn_arch['reg_fn']['beta'])
    rnn_learner.clip = nn_arch['clip']

    logging.info(rnn_learner)

    try:
        rnn_learner.load(dataset_name)
        calculate_and_display_metrics(rnn_learner, nn_params['metrics'], text_field.vocab)
    except FileNotFoundError:
        logging.warning(f"Model {dataset_name} not found. Training from scratch")

    if nn_params['mode'] is Mode.LEARNING_RATE_FINDING and run_training:
        logging.info("Looking for the best learning rate...")
        rnn_learner.lr_find()

        dir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(dir, path_to_model, 'lr_finder_plot.png')
        rnn_learner.sched.plot(path)
        logging.info(f"Plot is saved to {path}")
    elif nn_params['mode'] is Mode.TRAINING and run_training:
        training_start_time = time()
        vals, ep_vals = rnn_learner.fit(nn_arch['lr'], n_cycle=nn_arch['cycle']['n'], wds=nn_arch['wds'],
                        cycle_len=nn_arch['cycle']['len'], cycle_mult=nn_arch['cycle']['mult'],
                        metrics=list(map(lambda x: getattr(metrics, x), nn_arch['training_metrics'])),
                        cycle_save_name=dataset_name, get_ep_vals=True)
        training_time_mins = int(time() - training_start_time) // 60
        with open(f'{path_to_model}/results.out', 'w') as f:
            f.write(str(training_time_mins) + "\n")
            for _, vals in ep_vals.items():
                f.write(" ".join(map(lambda x:str(x), vals)) + "\n")

        logging.info(f'Saving model: {dataset_name}/{model_name}')
        rnn_learner.save(dataset_name)
        rnn_learner.save_encoder(dataset_name + "_encoder")
    else:
        logging.warning('No training...learning mode is off')

    return rnn_learner, text_field

def run_and_display_tests(m, text_field, path_to_save):
    to_test_mode(m)
    print("==============        TESTS       ====================")

    text = gen_text(m, text_field, nn_testing["starting_words"], nn_testing["how_many_words"])

    beautified_text = beautify_text(text)
    print(beautified_text)
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
    return keys[keys[:-2].rindex('\'') + 1:-2]


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


if __name__ =='__main__':
    logging.info("Using GPU: " + str(USE_GPU))
    logging.info("Using the following parameters:")
    logging.info(nn_arch)
    path_to_dataset = f'{nn_params["path_to_data"]}/{nn_params["dataset_name"]}'
    run_if_already_run = True
    folder, config_diff = find_most_similar_config(path_to_dataset, nn_arch)
    if config_diff != {}: #nn wasn't run with this config yet
        name = find_name_for_new_config(config_diff) if folder is not None else "baseline"
        path_to_model = f'{path_to_dataset}/{name}'
        os.mkdir(path_to_model)
        with open(f'{path_to_model}/{PARAM_FILE_NAME}', 'w') as f:
            json.dump(nn_arch, f)
        # with open(f'{path_to_dataset}/{name}/config_diff.json', 'w') as f:
        #     json.dump(config_diff, f)
        rnn_learner, text_field = get_language_model(name)
    else:
        path_to_model = f'{path_to_dataset}/{folder}'
        rnn_learner, text_field = get_language_model(folder, run_if_already_run)
    m=rnn_learner.model
    run_and_display_tests(m, text_field, f'{path_to_model}/gen_text.out')
