import argparse
import logging
import sys

logger = logging.getLogger(__name__)

def encode(words, merges):
    letters_list = {" ".join(k): v for k, v in words.items()}

    new_letters_list = {}
    for letters, freq in letters_list.items():
        subwords = letters.split(" ")
        while True:
            merge_index = None
            merge_candidate_priority = sys.maxsize
            for i in range(len(subwords) - 1):
                merge_candidate = (subwords[i], subwords[i + 1])
                if merge_candidate in merges:
                    if merges[merge_candidate] < merge_candidate_priority:
                        merge_candidate_priority = merges[merge_candidate]
                        merge_index = i
            if merge_index is None:
                break
            concat_pair = ''.join([subwords[merge_index], subwords[merge_index + 1]])
            del subwords[merge_index]
            del subwords[merge_index]
            subwords = subwords[:merge_index] + [concat_pair] + subwords[merge_index:]
        new_letters_list[" ".join(subwords)] = freq
    return new_letters_list


def read_merges(merges_file):
    merges = {}
    with open(merges_file, 'r') as f:
        for idx, line in enumerate(f):
            line = line.rstrip('\n')
            merges[tuple(line.split(" ")[:2])] = idx
    return merges


def encode_word(word, merges):
    enc_word, _ = encode({word: 0}, merges).popitem()
    subwords = enc_word.split(" ")
    return subwords


__all__ = [read_merges, encode_word]


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--merges-file', action='store', help='path to file with merges')
    arg_parser.add_argument('word', action='store', help='word to encode', default='if')
    arg_parser.add_argument('--input', action='store')
    arg_parser.add_argument('--output', action='store')

    from logrec.properties import DEFAULT_BPE_ENCODE_ARGS
    args = arg_parser.parse_args(*DEFAULT_BPE_ENCODE_ARGS)

    merges = read_merges(args.merges_file)

    if args.input and args.output:
        # working with files
        words = io.read_dict_from_2_columns(args.input)
        new_words = encode(words, merges)
        io.dump_dict_into_2_columns(new_words, args.output)
    else:
        subwords = encode_word(args.word, merges)
        print(subwords)
