import argparse
import logging
import re, collections

from logrec.local_properties import DEFAULT_BPE_ARGS
from logrec.util import io_utils
from logrec.util.priority_counter import PriorityCounter

logger = logging.getLogger(__name__)

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


VOCAB_FILE_NAME = "vocab"
REASSEMBLED_VOCAB_FILE_NAME = "vocab_reassembled.txt"
MERGES_FILE_NAME = "merges.txt"
MERGES_CACHE_FILE_NAME = "merges_cache.txt"
RESULTING_VOCAB_FILE_NAME = "vocab_res.txt"


def run(reset, base_dir, n_merges):
    vocab = {}
    if reset:
        logger.info("Starting the encoding from scratch...")
        with open(f'{base_dir}/{VOCAB_FILE_NAME}', 'r') as f:
            for line in f:
                line = line[:-1] if line[-1] == '\n' else line
                splits = line.split(" ")
                if len(splits) != 2:
                    raise ValueError(f"Invalid vocab line: {splits}")
                vocab[" ".join(splits[0])] = int(splits[1])
    else:
        logger.info("Using existing merges...")
        with open(f'{base_dir}/{REASSEMBLED_VOCAB_FILE_NAME}', 'r') as f:
            for line in f:
                line = line[:-1] if line[-1] == '\n' else line
                splits = line.split("\t")
                vocab[" ".join(splits[:-1])] = int(splits[-1])
    pairs = get_stats(vocab)

    merges = []
    if not reset:
        with open(f'{base_dir}/{MERGES_FILE_NAME}', 'r') as f:
            for line in f:
                line = line[:-1] if line[-1] == '\n' else line
                merges.append(line.split("\t"))
    n_done_merges = len(merges)
    for i in range(n_merges):
        try:
            best = pairs.pop_pair()
            print(f'Processing pair number {n_done_merges + i+1} ({best})')
            merges.append(best)
        except KeyError:
            break
        vocab = merge_vocab(best, vocab, pairs)

    resulting_vocab = collections.defaultdict(int)
    for entry, frequency in vocab.items():
        for subword in entry.split("\t"):
            resulting_vocab[subword] += frequency
    resulting_vocab_sorted = sorted(resulting_vocab.items(), key=lambda x: x[1], reverse=True)

    merges_cache = {}
    for entry, frequency in vocab.items():
        subword_list = entry.split('\t')
        key = ''.join(subword_list)
        merges_cache[key] = subword_list

    io_utils.dump_dict_into_2_columns(merges, f'{base_dir}/{MERGES_FILE_NAME}', append=True)
    io_utils.dump_dict_into_2_columns(vocab, f'{base_dir}/{REASSEMBLED_VOCAB_FILE_NAME}')
    io_utils.dump_dict_into_2_columns(merges_cache, f'{base_dir}/{MERGES_CACHE_FILE_NAME}', val_type=list)
    io_utils.dump_dict_into_2_columns(resulting_vocab_sorted, f'{base_dir}/{RESULTING_VOCAB_FILE_NAME}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('--n-merges', action='store', type=int, default=1)
    argument_parser.add_argument('--base-dir', action='store',
                                 default='/home/hlib/thesis/log-recommender/')
    argument_parser.add_argument('--reset', action='store_true')
    args = argument_parser.parse_args(*DEFAULT_BPE_ARGS)

    run(args.reset, args.base_dir, args.n_merges)
