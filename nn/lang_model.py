import logging
import pandas

import torch
from functools import partial

from fastai.metrics import accuracy, top_k
from fastai.nlp import LanguageModelData, seq2seq_reg
from params import em_sz, nh, nl, PATH, bs, bptt, TEXT, pretrained_lang_model_name
from utils import to_test_mode, output_predictions, gen_text, back_to_train_mode, f2, beautify_text
import dill as pickle

logging.basicConfig(level=logging.DEBUG)

def get_language_model(text_field, model_name):
    PATH_TO_MODEL=f'{PATH}/{model_name}'

    TRAIN_CONTEXTS = f'{PATH_TO_MODEL}/train/contexts.src'
    TEST_CONTEXTS = f'{PATH_TO_MODEL}/test/contexts.src'

    with open(TRAIN_CONTEXTS, 'r') as f:
        train_df = pandas.DataFrame([line for line in f])

    with open(TEST_CONTEXTS, 'r') as f:
        test_df = pandas.DataFrame([line for line in f])

    languageModelData = LanguageModelData.from_dataframes(PATH, text_field, 0, train_df, test_df, test_df,
                                                          bs=bs,
                                                          bptt=bptt,
                                                          min_freq=0
                                                          # not important since we remove rare tokens during preprocessing
                                                          )
    pickle.dump(text_field, open(f'{PATH_TO_MODEL}/TEXT.pkl', 'wb'))

    logging.info(f'Dictionary size is: {len(text_field.vocab.itos)}')

    opt_fn = partial(torch.optim.Adam, betas=(0.7, 0.99))

    rnn_learner = languageModelData.get_model(opt_fn, em_sz, nh, nl, dropouti=0.05,
                                              dropout=0.05, wdrop=0.1, dropoute=0.02,
                                              dropouth=0.05)
    rnn_learner.reg_fn = partial(seq2seq_reg, alpha=2, beta=1)
    rnn_learner.clip = 0.3

    logging.info(rnn_learner)

    try:
        rnn_learner.load(model_name)
        accuracies, examples = top_k(*rnn_learner.predict_with_targs(True), [1,10,100], 2)
        exs = []
        for input, num, preds, target in examples:
            exs.append((
                beautify_text(" ".join([text_field.vocab.itos[inp]
                                        if ind != num + 1 else "[[["+text_field.vocab.itos[inp]+"]]]"
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

    except FileNotFoundError:
        logging.warning(f"Model {model_name} not found. Training from scratch")

    # rnn_learner.lr_find()
    # rnn_learner.sched.plot()

    rnn_learner.fit(1e-3, n_cycle=2, wds=1e-6, cycle_len=1, cycle_mult=2, metrics=[accuracy, f2])

    logging.info(f'Saving model: {model_name}')
    # rnn_learner.save(model_name)
    # rnn_learner.save_encoder(model_name + "_encoder")

    return rnn_learner


rnn_learner = get_language_model(text_field=TEXT, model_name=pretrained_lang_model_name)
m=rnn_learner.model

to_test_mode(m)
print("==============        TESTS       ====================")

tests = [
"\\t2 try { \\t3 for ( sql <identifiersep> command command",
"\\t2 try { \\t3 if ( command . is <identifiersep> query ( )",
"\\t4 file file = new"
]
for starting_text in tests:
    output_predictions(m, TEXT, TEXT, starting_text, 3)
text = gen_text(m, TEXT, "public <identifier> ( ) throws", 500)
print(text)
print(beautify_text(text))

back_to_train_mode(m, bs)