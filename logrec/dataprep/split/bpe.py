import argparse
import logging
import re, collections

from logrec.local_properties import DEFAULT_BPE_ARGS
from logrec.util.priority_counter import PriorityCounter


def get_stats(vocab):
    pairs = collections.defaultdict(int)
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols) - 1):
            pairs[symbols[i], symbols[i + 1]] += freq
    return PriorityCounter(pairs)


def merge_vocab(pair, v_in, pairs):
    v_out = {}
    concat_pair_with_space = ' '.join(pair)
    concat_pair_with_space_escaped = re.escape(concat_pair_with_space)
    p = re.compile(r'(?<!\S)' + concat_pair_with_space_escaped + r'(?!\S)')
    concat_pair = ''.join(pair)
    concat_pair_escaped = re.escape(concat_pair)
    reg1 = re.compile('(\S+) (' + concat_pair_escaped + ')')
    reg2 = re.compile('(' + concat_pair_escaped + ') (\S+)')
    for word in v_in:
        w_out = p.sub(repr(concat_pair)[1:-1], word)
        v_out[w_out] = v_in[word]
        if word != w_out:
            # word changed
            m1 = re.search(reg1, w_out)
            if m1:
                pairs.add((m1.group(1), concat_pair), v_out[w_out])
                pairs.add((m1.group(1), pair[0]), -v_out[w_out])
            m2 = re.search(reg2, w_out)
            if m2:
                pairs.add((concat_pair, m2.group(2)), v_out[w_out])
                pairs.add((pair[1], m2.group(2)), -v_out[w_out])
    return v_out


VOCAB_FILE_NAME = "vocab.txt"
REASSEMBLED_VOCAB_FILE_NAME = "vocab_reassembled.txt"
MERGES_FILE_NAME = "merges.txt"
RESULTING_VOCAB_FILE_NAME = "vocab_res.txt"

if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('--n-merges', action='store', type=int, default=1)
    argument_parser.add_argument('--base-dir', action='store',
                                 default='/home/hlib/thesis/log-recommender/nn-data/devanbu_split_no_tabs_new_splits3_under_5000_15_percent/')
    argument_parser.add_argument('--reset', action='store_true')
    args = argument_parser.parse_args(*DEFAULT_BPE_ARGS)

    logging.basicConfig(level=logging.DEBUG)

    vocab = {}
    if args.reset:
        logging.info("Starting the encoding from scratch...")
        with open(f'{args.base_dir}/{VOCAB_FILE_NAME}', 'r') as f:
            for line in f:
                line = line[:-1] if line[-1] == '\n' else line
                splits = line.split(" ")
                vocab[" ".join(splits[0])] = int(splits[1])
    else:
        logging.info("Using existing merges...")
        with open(f'{args.base_dir}/{REASSEMBLED_VOCAB_FILE_NAME}', 'r') as f:
            for line in f:
                line = line[:-1] if line[-1] == '\n' else line
                splits = line.split(" ")
                vocab[" ".join(splits[:-1])] = int(splits[-1])
    pairs = get_stats(vocab)

    merges = []
    if not args.reset:
        with open(f'{args.base_dir}/{MERGES_FILE_NAME}', 'r') as f:
            for line in f:
                line = line[:-1] if line[-1] == '\n' else line
                merges.append(line.split(" "))
    n_done_merges = len(merges)
    for i in range(args.n_merges):
        try:
            best = pairs.pop_pair()
            print(f'Processing pair number {n_done_merges + i+1} ({best})')
            merges.append(best)
        except KeyError:
            break
        vocab = merge_vocab(best, vocab, pairs)

    resulting_vocab = collections.defaultdict(int)
    for entry, frequency in vocab.items():
        for subword in entry.split(" "):
            resulting_vocab[subword] += frequency
    resulting_vocab_sorted = sorted(resulting_vocab.items(), key=lambda x: x[1], reverse=True)

    with open(f'{args.base_dir}/{MERGES_FILE_NAME}', 'w+') as f:
        for merge in merges:
            f.write(" ".join(merge) + "\n")
    with open(f'{args.base_dir}/{REASSEMBLED_VOCAB_FILE_NAME}', 'w') as f:
        for entry, freq in vocab.items():
            f.write(f'{entry} {freq}\n')
    with open(f'{args.base_dir}/{RESULTING_VOCAB_FILE_NAME}', 'w') as f:
        for entry, freq in resulting_vocab_sorted:
            f.write(f'{entry} {freq}\n')