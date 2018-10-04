import logging

import torch

from fastai.core import to_np, to_gpu
from fastai.metrics import top_k, MRR

logging.basicConfig(level=logging.DEBUG)


def output_predictions(m, input_field, output_field, starting_text, how_many, file_to_save):
    words = [starting_text.split()]
    t=to_gpu(input_field.numericalize(words, -1))

    res,*_ = m(t)

    #==========================output predictions

    probs, labels = torch.topk(res[-1], how_many)
    text = ""
    text += ("===================" + "\n")
    text += (beautify_text(starting_text) + "\n")
    for probability, label in map(to_np, zip(probs, labels)):
        uu = f'{output_field.vocab.itos[label[0]]}: {probability}'
        text += (uu + "\n")
    return text


def gen_text(m, text_field, starting_words, how_many_to_gen):
    text = ''
    t = to_gpu(text_field.numericalize([starting_words.split()], -1))
    res, *_ = m(t)
    for i in range(how_many_to_gen):
        n = torch.multinomial(res[-1].exp(), 1)
        # n = n[1] if n.data[0] == 0 else n[0]
        text += text_field.vocab.itos[n.data[0]] + ' '
        res, *_ = m(n[0].unsqueeze(0))
    text += '...'
    return text

def beautify_text(text):
    text = text.replace('<eos>', '\n').replace('\\n', '\n').replace('<ect>', '\n\n').replace('<identifiersep>', '_')
    for i in range(1,11):
        text = text.replace('\\t'+str(i), ' ' * 4 * i)
    text = text.replace(' _ ', '_').replace(' . ', '.')
    return text


def to_test_mode(m):
    # Set batch size to 1
    m[0].bs = 1
    # Turn off dropout
    m.eval()
    # Reset hidden state
    m.reset()


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
        logging.info(f'                    ... {ex[0]}')
        logging.info(f'                    ... {ex[1]}')
        logging.info(f'                    ... {ex[2]}')
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