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


def get_language_model():
    model_name = nn_arch["model_name"]
    PATH_TO_MODEL= f'{nn_arch["path_to_data"]}/{model_name}'

    train_df = create_df(f'{PATH_TO_MODEL}/train/')
    test_df = create_df(f'{PATH_TO_MODEL}/test/')

    text_field = data.Field()
    languageModelData = LanguageModelData.from_dataframes(nn_arch["path_to_data"], text_field, 0, train_df, test_df, test_df,
                                                          bs=nn_arch["bs"],
                                                          bptt=nn_arch["bptt"],
                                                          min_freq=nn_arch["min_freq"]
                                                          # not important since we remove rare tokens during preprocessing
                                                          )
    pickle.dump(text_field, open(f'{PATH_TO_MODEL}/TEXT.pkl', 'wb'))

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
        rnn_learner.load(model_name)
        calculate_and_display_metrics(rnn_learner, nn_params['metrics'], text_field.vocab)
    except FileNotFoundError:
        logging.warning(f"Model {model_name} not found. Training from scratch")

    if nn_params['mode'] is Mode.LEARNING_RATE_FINDING:
        logging.info("Looking for the best learning rate...")
        rnn_learner.lr_find()

        dir = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(dir, '..', 'plot.png')
        rnn_learner.sched.plot(path)
        logging.info(f"Plot is saved to {path}")
    elif nn_params['mode'] is Mode.TRAINING:
        rnn_learner.fit(nn_arch['lr'], n_cycle=nn_arch['cycle']['n'], wds=nn_arch['wds'],
                        cycle_len=nn_arch['cycle']['len'], cycle_mult=nn_arch['cycle']['mult'],
                        metrics=list(map(lambda x: getattr(metrics, x), nn_arch['training_metrics'])))

        logging.info(f'Saving model: {model_name}')
        rnn_learner.save(model_name)
        rnn_learner.save_encoder(model_name + "_encoder")
    else:
        logging.warning('No training...learning mode is off')

    return rnn_learner, text_field

def run_and_display_tests(m, text_field):
    to_test_mode(m)
    print("==============        TESTS       ====================")

    text = gen_text(m, text_field, nn_testing["starting_words"], nn_testing["how_many_words"])
    print(text)
    print(beautify_text(text))

    back_to_train_mode(m, nn_arch['bs'])

if __name__ =='__main__':
    logging.info("Using GPU: " + str(USE_GPU))
    logging.info("Using the following parameters:")
    logging.info(nn_arch)

    rnn_learner, text_field = get_language_model()
    m=rnn_learner.model
    run_and_display_tests(m, text_field)
