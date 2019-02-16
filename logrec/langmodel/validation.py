import logging
import math
import random

import torch
from torchtext.data import Field

import fastai
from fastai.core import to_np, V, Variable, np, no_grad_context, VV, to_gpu
from fastai.metrics import mrr
from logrec.config.model import Cache
from logrec.dataprep.full_word_iterator import FullWordIterator
from logrec.langmodel.metrics import subword_aware_accuracy, subword_aware_accuracy_strict
from logrec.util.profiler import profile

logger = logging.getLogger(__name__)


@profile
def one_hot(idx, size):
    a = np.zeros((1, size), np.float32)  # TODO change to Byte
    a[0][idx] = 1
    v = VV(torch.from_numpy(a))
    return to_gpu(v)


@profile
def log_cache(targets, idx, p, ptr_dist, vocab_loss, text_field):
    index = targets[idx].data[0]
    logger.info(f"========================================")
    logger.info(f"Actual word: {text_field.vocab.itos[index]}")
    logger.info("Result:")
    vals, indices = torch.topk(p[0], 3)
    for c, i in zip(vals, indices):
        logger.info(f"{text_field.vocab.itos[i.data[0]]} ({c.data[0]})")
    logger.info("From cache:")
    vals, indices = torch.topk(ptr_dist[0], 3)
    for c, i in zip(vals, indices):
        logger.info(f"{text_field.vocab.itos[i.data[0]]} ({c.data[0]})")
    logger.info("From nn:")
    vals, indices = torch.topk(vocab_loss[0], 3)
    for c, i in zip(vals, indices):
        logger.info(f"{text_field.vocab.itos[i.data[0]]} ({c.data[0]})")


@profile
def cache_calc(preds_softmax: Variable, start_idx: int, next_word_history: Variable, pointer_history: Variable,
               last_hidden_layer_activations: Variable, targets: Variable, cache: Cache, text_field: Field) -> Variable:
    """

    :param preds_softmax:  bs x vocab_size
    :param start_idx:
    :param next_word_history: at most window x bs x vocab_siz
    :param pointer_history:
    :param last_hidden_layer_activations:
    :param targets:
    :param cache:
    :param text_field:
    :return:
    """
    preds_with_cache = []
    for idx, vocab_loss in enumerate(preds_softmax):
        p = vocab_loss
        if start_idx + idx > cache.window:
            valid_next_word = next_word_history[
                              start_idx + idx - cache.window:start_idx + idx]  # window x bs x vocab_size
            valid_pointer_history = pointer_history[
                                    start_idx + idx - cache.window:start_idx + idx]  # window x bs x vocab_size
            logits = torch.matmul(
                valid_pointer_history.transpose(0, 1),  # bs x window x vocab_size
                last_hidden_layer_activations[idx].unsqueeze(-1)  # bs x vocab_size x 1
            )  # bs x window x 1
            ptr_attn = torch.nn.functional.softmax(cache.theta * logits, dim=1).transpose(0, 1)  # window x bs
            ptr_dist = (ptr_attn.expand_as(valid_next_word) * valid_next_word).sum(0).squeeze()  # bs x vocab_size
            p = cache.lambdah * ptr_dist + (1 - cache.lambdah) * vocab_loss  # bs x vocab_size

            log_cache(targets, idx, p, ptr_dist, vocab_loss, text_field)
        ###
        preds_with_cache.append(p)
    return torch.stack(preds_with_cache)


def log(full_word_preds, full_word_pred_values, full_word_targets, full_word_accuracy, full_word_accuracy_strict,
        full_word_loss, text_field):
    logger.info(
        " ".join(map(lambda p, t: f'{text_field.vocab.itos[p]} ({t})', full_word_pred_values, full_word_targets)))
    logger.info(f'Full word acc: {full_word_accuracy:.3f}')
    lss = list(map(lambda x: -math.log(x), full_word_preds))
    logger.info(f'{full_word_loss:.3f}' + " " + str(list(map(lambda x: f'{x:.3f}', lss))) + f'= {sum(lss):.3f}')
    logger.info(f'Full word acc strict: {full_word_accuracy_strict:.3f}')
    lss = list(map(lambda x: -math.log(x), full_word_preds))
    logger.info(f'{full_word_loss:.3f}' + " " + str(list(map(lambda x: f'{x:.3f}', lss))) + f'= {sum(lss):.3f}')
    logger.info("============================")


def iterate_to_create_tensors(full_word_iterators):
    full_words_all_iterators = [
        [(full_word_targets, full_word_index_range) for full_word_targets, full_word_index_range in iterator]
        for iterator in full_word_iterators]
    chunks_left = [iterator.get_chunks_left() for iterator in full_words_all_iterators]
    max_n_full_words = max(lambda l: len(l), full_words_all_iterators)
    if max_n_full_words == 0:
        return None, 0, chunks_left

    biggest_index = max(lambda l: l[-1][1][1], full_words_all_iterators)

    ts = []
    n_words = 0
    for full_words in full_words_all_iterators:
        t = torch.zeros((max_n_full_words, biggest_index))
        for i, (full_word_targets, full_word_index_range) in enumerate(full_words):
            t[i, full_word_index_range[0]:full_word_index_range[1]] = 1
            n_words += 1
        ts.append(t)
    full_word_mask = torch.stack(ts)

    return full_word_mask, n_words, chunks_left


def calc_subword_aware_metrics():
    # actual_probs.extend(this_batch_actual_probs)
    # pred_vals.extend(this_batch_pred_vals)
    #
    # if not full_word_iterators:
    #     full_word_iterators = [FullWordIterator() for i in range(batch_size)]
    # for i in range(batch_size):
    #     full_word_iterators[i].add_data([text_field.vocab.itos[target] for target in targets[:, i]])
    # full_word_masks, n_words, chunks_left = iterate_to_create_tensors(full_word_iterators)
    # if full_word_masks is None:
    #     pass  # TODO
    #
    # full_word_loss = subword_aware_entropy_loss(actual_probs)
    #
    # full_word_targets_ints = [text_field.vocab.stoi[target] for target in full_word_targets]
    # full_word_accuracy = subword_aware_accuracy(pred_vals, full_word_targets_ints)
    # full_word_accuracy_strict = subword_aware_accuracy_strict(pred_vals,
    #                                                           full_word_targets_ints)
    #
    # actual_probs = actual_probs[-chunks_left:] if chunks_left > 0 else []
    # pred_vals = pred_vals[-chunks_left:] if chunks_left > 0 else []
    return None


@profile
def custom_validate(cache: Cache, text_field: Field, use_subword_aware_metrics: bool, stepper, dl, metrics, epoch,
                    seq_first, validate_skip):
    if use_subword_aware_metrics:
        raise ValueError("use_subword_aware_metrics=True is curreently not implemented")
    if cache:
        logger.info(f"Using neural cache with theta: {cache.theta}, lambdah: {cache.lambdah}, window: {cache.window}.")
    else:
        logger.info(f"Not using neural cache!")

    avg_batch_losses = []
    avg_batch_accuracies = []
    avg_batch_accuracies_strict = []
    actual_probs, pred_vals = [], []
    n_words_list = []
    stepper.reset(False)
    full_word_iterators = None
    with no_grad_context():
        next_word_history = None
        pointer_history = None
        n_iter = len(dl)
        for i, (*x, flattened_targets) in enumerate(iter(dl)):
            logger.info(f'Iteration {i} out of {n_iter}')
            x = VV(x)
            flattened_targets = VV(flattened_targets)

            flattened_preds, all_layers_hidden_activations, _ = stepper.evaluate_with_cache(x, flattened_targets)
            batch_size = x[0].size(1)
            vocab_size = flattened_preds.size(1)

            flattened_preds_softmax = torch.nn.functional.softmax(flattened_preds, dim=-1)
            if cache:
                start_idx = len(next_word_history) if next_word_history is not None else 0

                targets = flattened_targets.view(-1, batch_size)  # bptt x bs
                one_hot_encoded_targets = torch.stack(
                    [torch.cat([one_hot(target.data[0], vocab_size) for target in i_target_in_batch], dim=0)
                     for i_target_in_batch in targets])  # bptt x bs x vocab_size [290x32x5000x4=185MB]
                next_word_history = one_hot_encoded_targets if next_word_history is None \
                    else torch.cat([next_word_history, one_hot_encoded_targets])

                last_hidden_layer_activations = all_layers_hidden_activations[-1]  # bptt x batch size x layer size
                last_history_var = VV(last_hidden_layer_activations.data)
                pointer_history = last_history_var if pointer_history is None \
                    else torch.cat([pointer_history, last_history_var], dim=0)  # at most window x bs x layer_size

                preds_softmax = flattened_preds_softmax.view(-1, batch_size, vocab_size)  # bptt x bs x vocab_size
                predictions = cache_calc(preds_softmax=preds_softmax,
                                         start_idx=start_idx,
                                         next_word_history=next_word_history,
                                         pointer_history=pointer_history,
                                         last_hidden_layer_activations=last_hidden_layer_activations,
                                         targets=targets,
                                         cache=cache, text_field=text_field)

                next_word_history = next_word_history[-cache.window:]
                pointer_history = pointer_history[-cache.window:]
                flattened_predictions = predictions.view(-1, vocab_size)
            else:
                flattened_predictions = flattened_preds_softmax

            actual_probs = torch.gather(flattened_predictions, -1, flattened_targets.view(-1, 1))

            if use_subword_aware_metrics:
                pred_vals = torch.max(flattened_predictions, dim=-1)[1]
                cross_entropy_loss, accuracy, accuracy_strict, n_words = calc_subword_aware_metrics(pred_vals,
                                                                                                    actual_probs)
            else:
                n_words = flattened_targets.size(0)
                cross_entropy_loss = -torch.log(actual_probs).sum() / n_words
                accuracy = fastai.metrics.accuracy(flattened_predictions.data, flattened_targets)
                accuracy_strict = mrr(flattened_predictions.data, flattened_targets)

            avg_batch_losses.append(to_np(cross_entropy_loss))
            avg_batch_accuracies.append(accuracy)
            avg_batch_accuracies_strict.append(accuracy_strict)
            n_words_list.append(n_words)

        return [np.average(avg_batch_losses, 0, weights=n_words_list),
                np.average(avg_batch_accuracies, 0, weights=n_words_list),
                np.average(avg_batch_accuracies_strict, 0, weights=n_words_list)
                ]
