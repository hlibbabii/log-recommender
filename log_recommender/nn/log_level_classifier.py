import logging
from functools import partial
import pandas
import torch
from context_datasets import ContextsDataset

from fastai.lm_rnn import seq2seq_reg
from fastai.metrics import accuracy
from fastai.nlp import LanguageModelData, TextData
from params import nn_params

from utils import to_test_mode, back_to_train_mode, output_predictions
import dill as pickle
import numpy as np

logging.basicConfig(level=logging.DEBUG)

arch = nn_params['arch']

def get_text_classifier_model(text_field, level_label, model_name, pretrained_lang_model_name=None):

    splits = ContextsDataset.splits(text_field, level_label, path=f'{path_to_data}/{pretrained_lang_model_name}/')

    text_data = TextData.from_splits(nn_params['path_to_data'], splits, arch['bs'])
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
        rnn_learner.load(model_name)
        logging.info(f"Loaded model {model_name}. ")
    except FileNotFoundError:
        logging.warning(f"Model {model_name} not found. Training from pretrained lang model")
        try:
            rnn_learner.load_encoder(pretrained_lang_model_name + "_encoder")
        except FileNotFoundError:
            logging.error(f"Model {pretrained_lang_model_name}_encoder not found. Aborting...")
            exit(1)

    # rnn_learner.lr_find()
    # rnn_learner.sched.plot()

    rnn_learner.clip = 25.

    base_lr = 1e-3
    factor = 2.6
    lrs = np.array([
        base_lr / factor ** 4,
        base_lr / factor ** 3,
        base_lr / factor ** 2,
        base_lr / factor,
        base_lr])

    rnn_learner.freeze_to(-1)
    rnn_learner.fit(lrs, metrics=[accuracy], cycle_len=1, n_cycle=1)
    # rnn_learner.freeze_to(-2)
    # rnn_learner.fit(lrs, metrics=[accuracy], cycle_len=1, n_cycle=1)
    # rnn_learner.unfreeze()
    # rnn_learner.fit(lrs, metrics=[accuracy], cycle_len=1, n_cycle=1)

    # logging.info(f'Current accuracy is ...')
    # logging.info(f'                    ... {accuracy_gen(*rnn_learner.predict_with_targs())}')
    # rnn_learner.sched.plot_loss()

    logging.info(f'Saving classifier: {model_name}')
    # rnn_learner.save(model_name)

    return rnn_learner


text_field = pickle.load(open(f'{path_to_data}/{pretrained_lang_model_name}/TEXT.pkl', 'rb'))
learner = get_text_classifier_model(text_field, LEVEL_LABEL,
                                    model_name=pretrained_lang_model_name + '_classifier',
                                    pretrained_lang_model_name=pretrained_lang_model_name)

m=learner.model
to_test_mode(m)

# logging.info(f'Accuracy is {accuracy_np(*learner.predict_with_targs())}')

with open(f'{path_to_data}/{pretrained_lang_model_name}/test/contexts.src', 'r') as f:
    counter = 0
    for line in f:
        if counter > 30:
            break
        counter += 1
        print(f'{counter}\n')
        output_predictions(m, text_field, LEVEL_LABEL, line, 3)

back_to_train_mode(m, bs)

#plotting confusion matrix
# preds = np.argmax(probs, axis=1)
# probs = probs[:,1]
# from sklearn.metrics import confusion_matrix
# cm = confusion_matrix(y, preds)
# plot_confusion_matrix(cm, data.classes)