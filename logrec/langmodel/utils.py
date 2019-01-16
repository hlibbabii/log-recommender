import logging
import os
from typing import List, Union

from torch.cuda import current_device
from torchtext.data import Field

from fastai.core import to_np, to_gpu, F, USE_GPU, Variable
from fastai.lm_rnn import SequentialRNN
from fastai.metrics import top_k, MRR

import torch

from fastai.nlp import RNN_Learner
from logrec.dataprep.text_beautifier import beautify_text
from logrec.param.model import CONTEXT_SIDE_BEFORE, CONTEXT_SIDE_BOTH, CONTEXT_SIDE_AFTER

logger = logging.getLogger(__name__)


def get_predictions(model: SequentialRNN, input_field: Field, prepared_input: Union[List[str], List[List[str]]],
                    n_predictions: int) -> (Variable, Variable):
    t = to_gpu(input_field.numericalize(prepared_input, -1))
    res, *_ = model(t)
    outputs, labels = torch.topk(res[-1], n_predictions)
    probs = F.softmax(outputs)
    return probs, labels


def format_input(context_before: str, context_after: str, side: str) -> str:
    text = ("===================" + "\n")
    if side in [CONTEXT_SIDE_BEFORE, CONTEXT_SIDE_BOTH]:
        text += (beautify_text(context_before) + "\n")
        text += "\n"
    if side in [CONTEXT_SIDE_AFTER, CONTEXT_SIDE_BOTH]:
        text += (beautify_text(context_after) + "\n")
    return text


def format_predictions(probs: Variable, labels: Variable, output_field: Field, actual_label: str) -> str:
    text = ""
    for probability, label in map(to_np, zip(probs, labels)):
        uu = f'{output_field.vocab.itos[label[0]]}: {probability}'
        text += (uu + "\n")
    text += f'Actual label: {actual_label}\n'
    return text


def gen_text(learner: RNN_Learner, starting_words_list: List[str], how_many_to_gen: int) -> List[str]:
    text = []
    t = to_gpu(learner.text_field.numericalize([starting_words_list], -1))
    res, *_ = learner.model(t)
    for i in range(how_many_to_gen):
        n = torch.multinomial(res[-1].exp(), 1)
        # n = n[1] if n.data[0] == 0 else n[0]
        text.append(learner.text_field.vocab.itos[n.data[0]])
        res, *_ = learner.model(n[0].unsqueeze(0))
    return text


def to_test_mode(model: SequentialRNN):
    # Set batch size to 1gen_te
    model[0].bs = 1
    # Turn off dropout
    model.eval()
    # Reset hidden state
    model.reset()


def back_to_train_mode(m, bs):
    # Put the batch size back to what it was
    m[0].bs = bs

def display_not_guessed_examples(examples, vocab):
    exs = []
    for input, num, preds, target in examples:
        exs.append((
            beautify_text(" ".join([vocab.itos[inp]
                                    if ind != num + 1 else "[[[" + vocab.itos[inp] + "]]]"
                                    for ind, inp in enumerate(input)])),
            [vocab.itos[p] for p in preds],
            vocab.itos[target]
    ))
    for ex in exs:
        logger.info(f'                    ... {ex[0]}')
        logger.info(f'                    ... {ex[1]}')
        logger.info(f'                    ... {ex[2]}')
        logger.info(f'===============================================')


def calc_and_display_top_k(rnn_learner, metric, vocab):
    spl = metric.split("_")
    cat_index = spl.index("cat")
    if cat_index == -1 or len(spl) <= cat_index + 1:
        raise ValueError(f'Illegal metric format: {metric}')
    ks = list(map(lambda x: int(x), spl[1: cat_index]))
    cat = int(spl[cat_index + 1])

    accuracies, examples = top_k(*rnn_learner.predict_with_targs(True), ks, cat)

    logger.info(f'Current tops are ...')
    logger.info(f'                    ... {accuracies}')
    if spl[-1] == 'show':
        display_not_guessed_examples(examples, vocab)


def calculate_and_display_metrics(rnn_learner, metrics, vocab):
    for metric in metrics:
        if metric.startswith("topk"):
            calc_and_display_top_k(rnn_learner, metric, vocab)
        elif metric == 'mrr':
            mrr = MRR(*rnn_learner.predict_with_targs(True))
            logger.info(f"mrr: {mrr}")


def attach_dataset_aware_handlers_to_loggers(name, main_log_name):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(os.path.join(name, main_log_name), 'w')
    formatter = logging.Formatter("%(levelname)s - %(asctime)s :%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def printGPUInfo():
    logger.info("Using GPU: " + str(USE_GPU))
    if USE_GPU:
        logger.info("Number of GPUs available: " + str(torch.cuda.device_count()))
        logger.info(f"Using device: {current_device()}")
