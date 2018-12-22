import logging
import os
import shutil
from functools import partial

import dill as pickle
import numpy as np
import torch

from fastai.lm_rnn import seq2seq_reg
from fastai.metrics import accuracy
from fastai.nlp import TextData
from logrec.classifier.classifier import printGPUInfo
from logrec.classifier.classifier_params import LEVEL_LABEL, params
from logrec.classifier.context_datasets import ContextsDataset
from logrec.classifier.dataset_generator import WORDS_IN_CONTEXT_LIMIT
from logrec.dataprep import TEST_DIR, TEXT_FIELD_FILE, REPR_DIR, MODELS_DIR
from logrec.dataprep.preprocessors.preprocessing_types import PrepParamsParser
from logrec.langmodel.utils import to_test_mode, output_predictions, back_to_train_mode
from logrec.util.io_utils import file_mapper

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

arch = params['arch']

EXAMPLES_TO_SHOW = 100

def load_pretrained_langmodel(rnn_learner, dataset_name, pretrained_langmodel):
    path_to_lang_model = os.path.join(rnn_learner.models_path, '../../../..', REPR_DIR, dataset_name,
                                      pretrained_langmodel, MODELS_DIR, f'{dataset_name}_encoder.h5')
    new_dir = os.path.join(rnn_learner.models_path, pretrained_langmodel)
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    new_file = os.path.join(new_dir, f'{dataset_name}_lm_encoder.h5')
    logger.info(f"Copying {path_to_lang_model} to {new_file}")
    shutil.copy(path_to_lang_model, new_file)
    logger.info("Training from pretrained lang model")
    try:
        encoder_name = os.path.join(pretrained_langmodel, f'{dataset_name}_lm_encoder')
        rnn_learner.load_encoder(encoder_name)
    except FileNotFoundError:
        logger.error(f"Model {encoder_name} not found. Aborting...")
        exit(1)


def get_text_classifier_model(text_field, level_label, path_to_log_location_dataset, lang_model_dataset_name,
                              base_model, threshold):
    splits = ContextsDataset.splits(text_field, level_label, path_to_log_location_dataset, threshold=threshold)

    text_data = TextData.from_splits(path_to_log_location_dataset, splits, arch["bs"])
    # text_data.classes

    opt_fn = partial(torch.optim.Adam, betas=(0.7, 0.99))

    rnn_learner = text_data.get_model(opt_fn, WORDS_IN_CONTEXT_LIMIT, arch['bptt'], arch['em_sz'], arch['nh'],
                                      arch['nl'],
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

    logger.info(f'Dictionary size is: {len(text_field.vocab.itos)}')
    logger.info(rnn_learner)

    try:
        rnn_learner.load(base_model)
        logger.info(f"Loaded classifier: {base_model}. ")
    except FileNotFoundError:
        logger.warning(f"Pretrained classifier model {base_model} not found.")
        load_pretrained_langmodel(rnn_learner, lang_model_dataset_name, base_model)

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
    rnn_learner.fit(lrs, metrics=[accuracy], cycle_len=1, n_cycle=1, cycle_mult=1
                    # file=f"{path_to_model}/training.log"
                    )
    # rnn_learner.freeze_to(-2)
    # rnn_learner.fit(lrs, metrics=[accuracy], cycle_len=1, n_cycle=1)
    # rnn_learner.unfreeze()
    # rnn_learner.fit(lrs, metrics=[accuracy], cycle_len=1, n_cycle=1)

    # logger.info(f'Current accuracy is ...')
    # logger.info(f'                    ... {accuracy_gen(*rnn_learner.predict_with_targs())}')
    # rnn_learner.sched.plot_loss()

    # logger.info(f'Saving classifier: {base_classifier}')
    # rnn_learner.save(model_name)

    return rnn_learner


CLASSIFIER_NAME_SUFFIX = "_location_classifier"


def read_lines(filename):
    with open(filename, 'r') as f:
        return f.readlines()


def show_tests(path_to_test_set, m, text_field):
    counter = 0
    for c_filename, l_filename in file_mapper(path_to_test_set, ContextsDataset._get_pair, extension='label'):
        c_file = None
        l_file = None
        try:
            c_file = open(c_filename, 'r')
            l_file = open(l_filename, 'r')
            for context, level in zip(c_file, l_file):
                if counter >= EXAMPLES_TO_SHOW:
                    return
                output_predictions(m, text_field, LEVEL_LABEL, context.rstrip("\n"), 2)
                counter += 1
        except FileNotFoundError:
            project_name = c_filename[:-len(ContextsDataset.FW_CONTEXTS_FILE_EXT)]
            logger.error(f"Project context not loaded: {project_name}")
            continue
        finally:
            if c_file is not None:
                c_file.close()
            if l_file is not None:
                l_file.close()
            # if counter > 30:
            #     break
            # counter += 1
            # print(f'{counter}\n')


def run():
    path_to_log_location_data = params['path_to_classification_data']
    dataset_name = params['dataset_name']
    base_model = params['base_model']
    printGPUInfo()

    path_to_langmodel_data = os.path.join(path_to_log_location_data, '..', '..', REPR_DIR)
    clas9n_dataset_name = PrepParamsParser.to_classification_prep_params(dataset_name)
    path_to_log_location_dataset = os.path.join(path_to_log_location_data, clas9n_dataset_name)

    text_field = pickle.load(open(os.path.join(path_to_langmodel_data, dataset_name, TEXT_FIELD_FILE), 'rb'))
    learner = get_text_classifier_model(text_field, LEVEL_LABEL, path_to_log_location_dataset, dataset_name,
                                        base_model=base_model, threshold=params['threshold'])

    logger.info(f"Saving model: {base_model}")
    learner.save(base_model)
    m = learner.model
    to_test_mode(m)

    # logger.info(f'Accuracy is {accuracy_np(*learner.predict_with_targs())}')
    # counter = 0
    path_to_test_set = os.path.join(path_to_log_location_dataset, TEST_DIR)

    show_tests(path_to_test_set, m, text_field)

    # plotting confusion matrix
    # preds = np.argmax(probs, axis=1)
    # probs = probs[:,1]
    # from sklearn.metrics import confusion_matrix
    # cm = confusion_matrix(y, preds)
    # plot_confusion_matrix(cm, data.classes)


if __name__ == '__main__':
    run()
