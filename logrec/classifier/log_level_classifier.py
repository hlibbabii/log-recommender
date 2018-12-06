import logging
from functools import partial

import dill as pickle
import numpy as np
import torch

from fastai.lm_rnn import seq2seq_reg
from fastai.metrics import accuracy
from fastai.nlp import TextData
from logrec.classifier.classifier_params import LEVEL_LABEL, params
from logrec.classifier.context_datasets import ContextsDataset
from logrec.langmodel.utils import to_test_mode, output_predictions, back_to_train_mode

logging.basicConfig(level=logging.DEBUG)

arch = nn_params['arch']


def get_text_classifier_model(text_field, level_label, base_classifier, base_langmodel=None):
    splits = ContextsDataset.splits(text_field, level_label, path=f'{path_to_data}/{base_langmodel}/')

    text_data = TextData.from_splits(params['path_to_data'], splits, arch['bs'])
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
        rnn_learner.load(base_classifier)
        logging.info(f"Loaded classifier: {base_classifier}. ")
    except FileNotFoundError:
        logging.warning(f"Model {base_classifier} not found. Training from pretrained lang model")
        try:
            rnn_learner.load_encoder(base_langmodel + "_encoder")
        except FileNotFoundError:
            logging.error(f"Model {base_langmodel}_encoder not found. Aborting...")
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

    logging.info(f'Saving classifier: {base_classifier}')
    # rnn_learner.save(model_name)

    return rnn_learner


CLASSIFIER_NAME_SUFFIX = "_location_classifier"

if __name__ == '__main__':
    path_to_data = params['path_to_data']
    pretrained_langmodel = params['pretrained_langmodel']
    text_field = pickle.load(open(f'{path_to_data}/{pretrained_langmodel}/TEXT.pkl', 'rb'))
    learner = get_text_classifier_model(text_field, LEVEL_LABEL,
                                        base_classifier=pretrained_langmodel + CLASSIFIER_NAME_SUFFIX,
                                        base_langmodel=pretrained_langmodel)

    m = learner.model
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

    # plotting confusion matrix
    # preds = np.argmax(probs, axis=1)
    # probs = probs[:,1]
    # from sklearn.metrics import confusion_matrix
    # cm = confusion_matrix(y, preds)
    # plot_confusion_matrix(cm, data.classes)
