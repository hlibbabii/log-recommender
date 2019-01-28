import argparse
import logging
import os
import re, collections
from typing import Optional, Dict

from logrec.dataprep import BPE_DIR, METADATA_DIR
from logrec.dataprep.model.placeholders import placeholders
from logrec.dataprep.util import read_dict_from_2_columns, read_list, dump_dict_into_2_columns, dump_list
from logrec.properties import DEFAULT_BPE_ARGS, DEFAULT_PARSED_DATASETS_DIR
from logrec.util.priority_counter import PriorityCounter
import time

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


def get_most_recent_bpe_dir(base_dir: str) -> Optional[str]:
    common_bpe_dir = os.path.join(base_dir, BPE_DIR)
    if not os.path.exists(common_bpe_dir):
        logger.warning(f'Directory {common_bpe_dir} does not exist!')
        return None
    subdirs = next(os.walk(common_bpe_dir))[1]
    max_number = 0
    for subdir in subdirs:
        try:
            num = int(subdir)
            if num > max_number:
                max_number = num
        except ValueError:
            pass
    if max_number != 0:
        return os.path.join(common_bpe_dir, str(max_number))
    else:
        logger.warning(f'No bpe dirs found inside {common_bpe_dir}')
        return None


def archive_existing_common_bpe_folder(base_dir: str) -> None:
    common_bpe_dir = os.path.join(base_dir, BPE_DIR)
    if os.path.exists(common_bpe_dir):
        logger.info(f'Archiving existing bpe dir. '
                    f'{common_bpe_dir} -> {common_bpe_dir}.{str(int(time.time()))}')
        os.rename(common_bpe_dir, f'{common_bpe_dir}.{str(int(time.time()))}')


def separate_non_splittable_vocab(all_vocab: Dict[str, int], from_reassambled: bool) -> (
Dict[str, int], Dict[str, int]):
    vocab = {}
    non_splitable_vocab = {}
    for k, v in all_vocab.items():
        placeholders_values = placeholders.values()
        if k not in placeholders_values:
            vocab[k if from_reassambled else " ".join(k)] = v
        else:
            non_splitable_vocab[k] = v
    return vocab, non_splitable_vocab


def run(dataset: str, repr: str, n_merges: int, reset: bool) -> None:
    base_dir = os.path.join(DEFAULT_PARSED_DATASETS_DIR, dataset, METADATA_DIR, repr)
    if reset:
        starting_from_scratch = True
        archive_existing_common_bpe_folder(base_dir)
    else:
        logger.info("Using existing merges...")
        most_recent_bpe_dir = get_most_recent_bpe_dir(base_dir)
        if not most_recent_bpe_dir:
            logger.warning("Existing merges not found ")
            starting_from_scratch = True
        else:
            all_vocab = read_dict_from_2_columns(
                os.path.join(most_recent_bpe_dir, REASSEMBLED_VOCAB_FILE_NAME))
            vocab, non_splitable_vocab = separate_non_splittable_vocab(all_vocab, from_reassambled=True)
            merges = read_list(os.path.join(most_recent_bpe_dir, MERGES_FILE_NAME))
            starting_from_scratch = False

    if starting_from_scratch:
        logger.info("Starting the encoding from scratch...")
        all_vocab = read_dict_from_2_columns(os.path.join(base_dir, VOCAB_FILE_NAME))
        vocab, non_splitable_vocab = separate_non_splittable_vocab(all_vocab, from_reassambled=False)
        merges = []

    pairs = get_stats(vocab)
    n_done_merges = len(merges)
    for i in range(n_merges):
        try:
            best = pairs.pop_pair()
            print(f'Processing pair number {n_done_merges + i+1} {best}')
            merges.append(best)
        except KeyError:
            break
        vocab = merge_vocab(best, vocab, pairs)

    for k, v in non_splitable_vocab.items():
        vocab[k] = v
    resulting_vocab = collections.defaultdict(int)
    for entry, frequency in vocab.items():
        for subword in entry.split(" "):
            resulting_vocab[subword] += frequency
    resulting_vocab_sorted = sorted(resulting_vocab.items(), key=lambda x: x[1], reverse=True)

    merges_cache = {}
    for entry, frequency in vocab.items():
        subword_list = entry.split(' ')
        key = ''.join(subword_list)
        merges_cache[key] = subword_list

    new_bpe_dir = os.path.join(base_dir, BPE_DIR, str(len(merges)))
    if os.path.exists(new_bpe_dir):
        raise AssertionError(f'Dir {new_bpe_dir} already exists? Something went wrong.'
                             f'Check the contents of {os.path.join(base_dir, BPE_DIR)} folder')
    os.makedirs(new_bpe_dir)

    dump_list(merges, os.path.join(new_bpe_dir, MERGES_FILE_NAME))
    dump_dict_into_2_columns(vocab, os.path.join(new_bpe_dir, REASSEMBLED_VOCAB_FILE_NAME))
    dump_dict_into_2_columns(merges_cache, os.path.join(new_bpe_dir, MERGES_CACHE_FILE_NAME), val_type=list)
    dump_dict_into_2_columns(resulting_vocab_sorted, os.path.join(new_bpe_dir, RESULTING_VOCAB_FILE_NAME))
    logger.info(f'Bpe output files are saved into {new_bpe_dir} folder')


if __name__ == '__main__':
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('dataset', action='store', help=f'dataset name')
    argument_parser.add_argument('repr', action='store', help=f'repr name')
    argument_parser.add_argument('n_merges', action='store', type=int)
    argument_parser.add_argument('--reset', action='store_true')

    args = argument_parser.parse_args(*DEFAULT_BPE_ARGS)

    run(args.dataset, args.repr, args.n_merges, args.reset)
