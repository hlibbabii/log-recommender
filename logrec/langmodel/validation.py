import logging
import math
from typing import List

import torch
from torchtext.data import Field

from fastai.core import to_np, V, Variable, np, no_grad_context, VV, to_gpu
from logrec.config.model import Cache
from logrec.dataprep.full_word_iterator import FullWordIterator

logger = logging.getLogger(__name__)


def one_hot(idx, size):
    a = np.zeros((1, size), np.float32)
    a[0][idx] = 1
    v = Variable(torch.from_numpy(a))
    return to_gpu(v)


def cache_calc(softmax_output_flat: Variable, start_idx: int, next_word_history: Variable, pointer_history: Variable,
               rnn_out: Variable, targets: Variable, cache: Cache) -> Variable:
    preds_with_cache = []
    for idx, vocab_loss in enumerate(softmax_output_flat):
        p = vocab_loss
        if start_idx + idx > cache.window:
            valid_next_word = next_word_history[start_idx + idx - cache.window:start_idx + idx]
            valid_pointer_history = pointer_history[start_idx + idx - cache.window:start_idx + idx]
            logits = torch.mv(valid_pointer_history, rnn_out[idx])
            ptr_attn = torch.nn.functional.softmax(cache.theta * logits).view(-1, 1)
            ptr_dist = (ptr_attn.expand_as(valid_next_word) * valid_next_word).sum(0).squeeze()
            p = cache.lambdah * ptr_dist + (1 - cache.lambdah) * vocab_loss
            index = targets[idx].data[0]
            # logger.info(f"========================================")
            # logger.info(f"Actual word: {text_field.vocab.itos[index]}")
            # logger.info("Result:")
            # vals, indices = torch.topk(p, 3)
            # for c, i in zip(vals, indices):
            #     logger.info(f"{text_field.vocab.itos[i.data[0]]} ({c.data[0]})")
            # logger.info("From cache:")
            # vals, indices = torch.topk(ptr_dist, 3)
            # for c,i in zip(vals, indices):
            #     logger.info(f"{text_field.vocab.itos[i.data[0]]} ({c.data[0]})")
            # logger.info("From nn:")
            # vals, indices = torch.topk(vocab_loss, 3)
            # for c,i in zip(vals, indices):
            #     logger.info(f"{text_field.vocab.itos[i.data[0]]} ({c.data[0]})")
        ###
        preds_with_cache.append(p)
    return torch.stack(preds_with_cache)


def calc_full_word_accuracy(subword_predictions: List[int], subword_targets: List[int]) -> float:
    for pred, target in zip(subword_predictions, subword_targets):
        if pred != target:
            return 0.0
    return 1.0


def calc_full_word_accuracy2(subword_predictions: List[int], subword_targets: List[int]) -> float:
    if len(subword_predictions) != len(subword_targets):
        raise ValueError(f'Lists should be of the same length: {subword_predictions}, {subword_targets}')
    sum = 0.0
    for pred, target in zip(subword_predictions, subword_targets):
        sum += (1.0 if pred == target else 0.0)

    return sum / len(subword_predictions)


def calc_full_word_loss(subword_probabilities: List[float]) -> float:
    full_word_loss = 0
    for pp in subword_probabilities:
        full_word_loss -= math.log(pp)
    return full_word_loss


def log(full_word_preds, full_word_pred_values, full_word_targets, full_word_accuracy, full_word_loss, text_field):
    logger.info(
        " ".join(map(lambda p, t: f'{text_field.vocab.itos[p]} ({t})', full_word_pred_values, full_word_targets)))
    logger.info(f'Full word acc: {full_word_accuracy:.3f}')
    lss = list(map(lambda x: -math.log(x), full_word_preds))
    logger.info(f'{full_word_loss:.3f}' + " " + str(list(map(lambda x: f'{x:.3f}', lss))) + f'= {sum(lss):.3f}')
    logger.info("============================")


def custom_validate(cache: Cache, split_repr: int, text_field: Field, stepper, dl, metrics, epoch, seq_first,
                    validate_skip):
    if cache:
        logger.info(f"Using neural cache with theta: {cache.theta}, lambdah: {cache.lambdah}, window: {cache.window}.")
    bptts, res = [], []
    avg_batch_losses = []
    avg_batch_accuracies = []
    actual_probs, pred_vals = [], []
    ps = []
    seqs_in_batch_list = []
    stepper.reset(False)
    with no_grad_context():
        next_word_history = None
        pointer_history = None
        if split_repr == 1:
            full_word_iterator = FullWordIterator()
        else:
            raise NotImplementedError("Iterator for split repr 0 is not yet implemented!")
        n_iter = len(dl)
        for i, (*x, targets) in enumerate(iter(dl)):
            logger.debug(f'Validation: {i}/{n_iter}')
            # x - [Variable(x1,x2, ... xn)]
            # y - Variable(x2...,xn, xn+1)
            batch_size = x[0].size(1)
            if batch_size != 1:
                raise ValueError("For now only batch size 1 is supported for validation with cache")
            preds, raw_outputs, l = stepper.evaluate_with_cache(VV(x), VV(targets))
            # preds [bptt x vocab size] Variable
            # raw_outputs [Variables[bptt x batch size x layer size], ...] - list, size: number of layers
            # l - cross entropy Variable [batch size]
            # targets [bptt]
            ntokens = preds.size(1)
            rnn_out = raw_outputs[-1].squeeze(1)  # from last layer
            output_flat = preds.view(-1, ntokens)

            seqs_in_batch = 0
            softmax_output_flat = torch.nn.functional.softmax(output_flat)
            bptts.append(softmax_output_flat.size(0))
            if cache:
                # Fill pointer history
                start_idx = len(next_word_history) if next_word_history is not None else 0
                next_word_history = torch.cat(
                    [one_hot(t.data[0], ntokens) for t in targets]) if next_word_history is None else torch.cat(
                    [next_word_history, torch.cat([one_hot(t.data[0], ntokens) for t in targets])])
                # print(next_word_history)
                pointer_history = Variable(rnn_out.data) if pointer_history is None else torch.cat(
                    [pointer_history, Variable(rnn_out.data)], dim=0)

                predictions = cache_calc(softmax_output_flat=softmax_output_flat,
                                         start_idx=start_idx,
                                         next_word_history=next_word_history,
                                         pointer_history=pointer_history,
                                         rnn_out=rnn_out,
                                         targets=targets,
                                         cache=cache)
                next_word_history = next_word_history[-cache.window:]
                pointer_history = pointer_history[-cache.window:]
            else:
                predictions = softmax_output_flat

            targets = targets.data
            predictions = predictions.data
            losses_in_batch = []
            accuracies_in_batch = []
            this_batch_pred_vals = torch.max(predictions, dim=1)[1]
            this_batch_actual_probs = torch.gather(predictions, 1, targets.view(-1, 1))
            actual_probs.extend(this_batch_actual_probs)
            pred_vals.extend(this_batch_pred_vals)
            target_tokens = [text_field.vocab.itos[target] for target in targets]
            full_word_iterator.add_data(target_tokens)
            for full_word_targets, full_word_index_range in full_word_iterator:
                full_word_actual_probs = actual_probs[full_word_index_range[0]: full_word_index_range[1]]
                full_word_pred_values = pred_vals[full_word_index_range[0]: full_word_index_range[1]]

                full_word_loss = calc_full_word_loss(full_word_actual_probs)
                full_word_targets_ints = [text_field.vocab.stoi[target] for target in full_word_targets]
                full_word_accuracy = calc_full_word_accuracy2(full_word_pred_values, full_word_targets_ints)
                seqs_in_batch += 1
                losses_in_batch.append(full_word_loss)
                accuracies_in_batch.append(full_word_accuracy)
                if seqs_in_batch == 1:
                    log(full_word_actual_probs, full_word_pred_values, full_word_targets, full_word_accuracy,
                        full_word_loss, text_field)
            chunks_left = full_word_iterator.get_chunks_left()
            actual_probs = actual_probs[-chunks_left:] if chunks_left > 0 else []
            pred_vals = pred_vals[-chunks_left:] if chunks_left > 0 else []

            # hidden = repackage_hidden(hidden)

            if seqs_in_batch > 0:
                avg_batch_loss = sum(losses_in_batch) / seqs_in_batch
                avg_batch_losses.append(to_np(V(avg_batch_loss)))

                avg_batch_accuracy = sum(accuracies_in_batch) / seqs_in_batch
                avg_batch_accuracies.append(to_np(V(avg_batch_accuracy)))

                seqs_in_batch_list.append(seqs_in_batch)

    return [np.average(avg_batch_losses, 0, weights=seqs_in_batch_list),
            np.average(avg_batch_accuracies, 0, weights=seqs_in_batch_list)[0]]
