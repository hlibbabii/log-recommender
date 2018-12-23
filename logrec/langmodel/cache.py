import logging

import torch

from fastai.core import to_np, V, Variable, np, no_grad_context, VV

logger = logging.getLogger(__name__)


def one_hot(idx, size, cuda=False):
    a = np.zeros((1, size), np.float32)
    a[0][idx] = 1
    v = Variable(torch.from_numpy(a))
    if cuda: v = v.cuda()
    return v


def validate_with_cache(get_full_word_func, stepper, dl, metrics, epoch, seq_first, validate_skip, text_field, theta=2,
                        lambdah=0.0, window=1000):
    logger.info(f"Using theta: {theta}, lambdah: {lambdah}")
    bptts, losses, res = [], [], []
    seq = []
    ps = []
    seqs_in_batch_list = []
    stepper.reset(False)
    with no_grad_context():
        next_word_history = None
        pointer_history = None
        for (*x, y) in iter(dl):
            # x - [Variable(x1,x2, ... xn)]
            # y - Variable(x2...,xn, xn+1)
            batch_size = x[0].size(1)
            if batch_size != 1:
                raise ValueError("For now only batch v  vfrsize 1 is supported for validation with cache")
            preds, raw_outputs, l, targets = stepper.evaluate_with_cache(VV(x), VV(y))
            # preds [bptt x vocab size] Variable
            # raw_outputs [Variables[bptt x batch size x layer size], ...] - list, size: number of layers
            # l - cross entropy Variable [batch size]
            # targets [bptt]
            ntokens = preds.size(1)
            rnn_out = raw_outputs[-1].squeeze(1)  # from last layer
            output_flat = preds.view(-1, ntokens)
            # Fill pointer history
            start_idx = len(next_word_history) if next_word_history is not None else 0
            next_word_history = torch.cat(
                [one_hot(t.data[0], ntokens) for t in targets]) if next_word_history is None else torch.cat(
                [next_word_history, torch.cat([one_hot(t.data[0], ntokens) for t in targets])])
            # print(next_word_history)
            pointer_history = Variable(rnn_out.data) if pointer_history is None else torch.cat(
                [pointer_history, Variable(rnn_out.data)], dim=0)

            loss = 0
            seqs_in_batch = 0
            softmax_output_flat = torch.nn.functional.softmax(output_flat)
            bptts.append(softmax_output_flat.size(0))
            preds_with_cache = []
            for idx, vocab_loss in enumerate(softmax_output_flat):
                p = vocab_loss
                if start_idx + idx > window:
                    valid_next_word = next_word_history[start_idx + idx - window:start_idx + idx]
                    valid_pointer_history = pointer_history[start_idx + idx - window:start_idx + idx]
                    logits = torch.mv(valid_pointer_history, rnn_out[idx])
                    ptr_attn = torch.nn.functional.softmax(theta * logits).view(-1, 1)
                    ptr_dist = (ptr_attn.expand_as(valid_next_word) * valid_next_word).sum(0).squeeze()
                    p = lambdah * ptr_dist + (1 - lambdah) * vocab_loss
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
                current_target = targets[idx].data
                current_p = p[current_target]
                curr_seq, current_ps, seq, ps = get_full_word_func(seq, ps, current_target, current_p, text_field)
                if curr_seq is not None:
                    for pp in current_ps:
                        loss += (-torch.log(pp)).data[0]
                    seqs_in_batch += 1
                    if len(current_ps) > 0:
                        logger.info(" ".join(map(lambda x: text_field.vocab.itos[x[0]], curr_seq)))
                        lss = list(map(lambda x: (-torch.log(x)).data[0], current_ps))
                        logger.info("" + str(list(map(lambda x: f'{x:.3f}', lss))) + f'= {sum(lss):.3f}')
                        logger.info("============================")
                preds_with_cache.append(p)
            ###
            # hidden = repackage_hidden(hidden)
            next_word_history = next_word_history[-window:]
            pointer_history = pointer_history[-window:]
            res.append([f(torch.stack(preds_with_cache).data, y) for f in metrics])

            if seqs_in_batch > 0:
                loss = loss / seqs_in_batch
                losses.append(to_np(V(loss)))

                seqs_in_batch_list.append(seqs_in_batch)

        for pp in ps:
            loss += (-torch.log(pp)).data[0]
        losses.append(to_np(V(loss)))
        seqs_in_batch_list.append(1)

    return [np.average(losses, 0, weights=seqs_in_batch_list)] + list(np.average(np.stack(res), 0, weights=bptts))
