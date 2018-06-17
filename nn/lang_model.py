import matplotlib
matplotlib.use('Agg')

import logging
import os

import pandas

import torch
from functools import partial

from fastai.core import USE_GPU
from fastai.metrics import accuracy, top_k, MRR, mrr_non_interactive
from fastai.nlp import LanguageModelData, seq2seq_reg
from params import TEXT, nn_params, Mode
from utils import to_test_mode, gen_text, back_to_train_mode, f2, beautify_text
import dill as pickle

logging.basicConfig(level=logging.DEBUG)


def calculate_and_display_metrics(text_field):
    accuracies, examples = top_k(*rnn_learner.predict_with_targs(True), [1, 10, 100], 2)

    exs = []
    for input, num, preds, target in examples:
        exs.append((
            beautify_text(" ".join([text_field.vocab.itos[inp]
                                    if ind != num + 1 else "[[[" + text_field.vocab.itos[inp] + "]]]"
                                    for ind, inp in enumerate(input)])),
            num,
            [text_field.vocab.itos[p] for p in preds],
            text_field.vocab.itos[target]
        ))

    logging.info(f'Current tops are ...')
    logging.info(f'                    ... {accuracies}')
    for ex in exs:
        logging.info(f'                    ... {ex[0]}')
        logging.info(f'                    ... {ex[1]}')
        logging.info(f'                    ... {ex[2]}')
        logging.info(f'                    ... {ex[3]}')
        logging.info(f'===============================================')
    mrr = MRR(*rnn_learner.predict_with_targs(True))
    logging.info(f"mrr: {mrr}")


def get_language_model(text_field, learning_mode=True, learning_rate_finding_mode = False):
    model_name = nn_params["model_name"]
    PATH_TO_MODEL= f'{nn_params["path_to_data"]}/{model_name}'

    TRAIN_CONTEXTS = f'{PATH_TO_MODEL}/train/contexts.src'
    TEST_CONTEXTS = f'{PATH_TO_MODEL}/test/contexts.src'

    with open(TRAIN_CONTEXTS, 'r') as f:
        train_df = pandas.DataFrame([line for line in f])

    with open(TEST_CONTEXTS, 'r') as f:
        test_df = pandas.DataFrame([line for line in f])

    languageModelData = LanguageModelData.from_dataframes(nn_params["path_to_data"], text_field, 0, train_df, test_df, test_df,
                                                          bs=nn_params["bs"],
                                                          bptt=nn_params["bptt"],
                                                          min_freq=nn_params["min_freq"]
                                                          # not important since we remove rare tokens during preprocessing
                                                          )
    pickle.dump(text_field, open(f'{PATH_TO_MODEL}/TEXT.pkl', 'wb'))

    logging.info(f'Dictionary size is: {len(text_field.vocab.itos)}')

    opt_fn = partial(torch.optim.Adam, betas=nn_params['betas'])

    rnn_learner = languageModelData.get_model(opt_fn, nn_params['em_sz'], nn_params['nh'], nn_params['nl'],
                                              dropouti=nn_params['drop']['outi'],
                                              dropout=nn_params['drop']['out'],
                                              wdrop=nn_params['drop']['w'],
                                              dropoute=nn_params['drop']['oute'],
                                              dropouth=nn_params['drop']['outh'])
    rnn_learner.reg_fn = partial(seq2seq_reg, alpha=nn_params['reg_fn']['alpha'], beta=nn_params['reg_fn']['beta'])
    rnn_learner.clip = nn_params['clip']

    logging.info(rnn_learner)

    try:
        rnn_learner.load(model_name)
        calculate_and_display_metrics(text_field)
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
        rnn_learner.fit(nn_params['lr'], n_cycle=nn_params['cycle']['n'], wds=nn_params['wds'],
                        cycle_len=nn_params['cycle']['len'], cycle_mult=nn_params['cycle']['mult'],
                        metrics=[accuracy, f2, mrr_non_interactive])

        logging.info(f'Saving model: {model_name}')
        rnn_learner.save(model_name)
        rnn_learner.save_encoder(model_name + "_encoder")
    else:
        logging.warning('No training...learning mode is off')

    return rnn_learner

def run_and_display_tests(m):
    to_test_mode(m)
    print("==============        TESTS       ====================")

    text = gen_text(m, TEXT, "public <identifier> ( ) throws", 500)
    print(text)
    print(beautify_text(text))

    back_to_train_mode(m, nn_params['bs'])

if __name__ =='__main__':
    logging.info("Using GPU: " + str(USE_GPU))
    rnn_learner = get_language_model(text_field=TEXT)
    m=rnn_learner.model
    run_and_display_tests(m)
