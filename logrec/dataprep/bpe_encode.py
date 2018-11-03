import argparse
import sys

from logrec.local_properties import DEFAULT_BPE_ENCODE_ARGS


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


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--merges-file', action='store', help='path to file with merges')
    arg_parser.add_argument('word', action='store', help='word to encode', default='if')
    arg_parser.add_argument('--input', action='store')
    arg_parser.add_argument('--output', action='store')
    args = arg_parser.parse_args(*DEFAULT_BPE_ENCODE_ARGS)

    merges = {}
    with open(args.merges_file, 'r') as f:
        for idx, line in enumerate(f):
            line = line[:-1] if line[-1] == '\n' else line
            merges[tuple(line.split(" "))] = idx

    if args.input and args.output:
        # working with files
        words = {}
        with open(args.input, 'r') as f:
            for line in f:
                line = line[:-1] if line[-1] else line
                splits = line.split(" ")
                words[splits[0]] = splits[1]
        new_words = encode(words, merges)
        with open(args.output, 'w') as f:
            for word, freq in new_words.items():
                f.write(f'{word} {freq}\n')
    else:
        word, _ = encode({args.word: 0}, merges).popitem()
        subwords = word.split(" ")
        print(subwords)
