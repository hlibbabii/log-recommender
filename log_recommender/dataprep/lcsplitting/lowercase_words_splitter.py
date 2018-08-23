import argparse
import json
import logging
import os
from math import log
from operator import itemgetter
from random import shuffle

from dataprep import base_project_dir
from dataprep.lcsplitting.split_cache import cache
from fastai.imports import tqdm

logging.basicConfig(level=logging.INFO)


def combos(s, max_words):
    if not s:
        return
    yield (s,)
    if max_words == 1:
        return
    for i in range(1, len(s)):
        for c in combos(s[i:], max_words - 1):
            yield (s[:i],) + c


def adjusted_negative_abs(x, alpha):
    return x if x >= 0 else -alpha * x


avg_length_of_most_frequent_words = 4.94

params = {
    'alpha': 9.0,
    'beta': 5.0,
    'gamma': 3.0,
    'lambda_': 1.8,
    'theta': 2.0,
    'd': 10.0
}

typo_params = {
    'denum_error_likelihood_param': 10.0,
    'error_likelihood_param': 4.0,
    'min_length_for_typo_detection': 8
}

max_subwords = [(10, 5), (15, 6), (30, 7), (1000, 8)]


def get_max_subwords(word):
    ln = len(word)
    for a, res in max_subwords:
        if ln <= a:
            return res


def ff(freq, occurs_in_general_dict, fullword, params):
    occurs_in_general_dict_points = params['d'] if occurs_in_general_dict and fullword else 1
    return log(freq + params['alpha']) ** params['theta'] * occurs_in_general_dict_points


def ll(word, params):
    return 1.0 / log(adjusted_negative_abs(len(word) - avg_length_of_most_frequent_words,
                                           params['beta']) + params['gamma'])


def get_splittings(words_to_split, freqs, general_dict, params):
    freqs = dict(sorted(freqs.items(), key=lambda x: len(x[0])))
    new_freqs = freqs.copy()
    transformed = {}
    nontransformed = []
    possible_typos = []

    for ind, (word, freq) in enumerate(tqdm(freqs.items(), leave=False, total=len(freqs))):
        if word not in words_to_split:
            continue
        # if ind >= 1000: break
        denum_f = ff(freq, word in general_dict, True, params)
        denum_l = ll(word, params)
        denum = denum_f * denum_l
        options = []
        if word in cache:
            combinations = cache[word]
        else:
            combinations = combos(word, get_max_subwords(word))
        for subwords_set in combinations:
            all_words_exist = True
            num = 0.0
            num_ls = []
            num_fs = []
            n = len(subwords_set)
            for subword in subwords_set:
                if subword in new_freqs:
                    num_fs.append(ff(new_freqs[subword], subword in general_dict, n == 1, params))
                    num_ls.append(ll(subword, params))
                    num += num_fs[-1] * num_ls[-1]
                else:
                    all_words_exist = False
            num = num * (1.0 / n ** params['lambda_'])
            if all_words_exist:
                result = num / denum
                options.append({
                    'subwords_set': subwords_set,
                    'num': num,
                    'denum': denum,
                    'results': result,
                    'denum_f': denum_f,
                    'denum_l': denum_l,
                    'num_fs': num_fs,
                    'num_ls': num_ls
                })
        options.sort(key=itemgetter('num'), reverse=True)
        if word not in cache:
            cache[word] = [opt['subwords_set'] for opt in options[:10]]
        for option in options[:5]:
            num_str = "avg(" + "+".join([f'{f:.2f}*{l:.2f}' for f, l in zip(option["num_fs"], option["num_ls"])]) + ")"
            logging.debug(
                f' {option["results"]:.2f}: {word} -> {option["subwords_set"]}:  {option["num"]:.2f}/{option["denum"]:.2f}='
                f'{num_str}/{option["denum_f"]:.2f}*{option["denum_l"]:.2f}')
        if len(options) <= 0:
            raise AssertionError(f"No split options for: {word}")
        if options[0]["denum"] < typo_params['denum_error_likelihood_param'] \
                and options[0]["results"] < typo_params['error_likelihood_param'] \
                and len(word) >= typo_params['min_length_for_typo_detection']:
            possible_typos.append(word)
        if options[0]["results"] > 1.0 and len(options[0]["subwords_set"]) > 1:
            transformed[word] = options[0]
            del (new_freqs[word])
        else:
            nontransformed.append(word)
        logging.debug("================================")
    return transformed, nontransformed, possible_typos


def load_english_dict(path_to_dict_dir):
    general_dict = {}
    for file in os.listdir(path_to_dict_dir):
        with open(f'{path_to_dict_dir}/{file}', 'r') as f:
            for line in f:
                general_dict[line[:-1].lower()] = 1
    return general_dict


if __name__ == '__main__':
    base_dir = base_from = f'{base_project_dir}/nn-data/new_framework/'

    parser = argparse.ArgumentParser()
    parser.add_argument('--path-to-dataset', action='store', default='100_percent/repr/nonewlinestabs_1_spl_1_numspl_1_nostrcom_1')
    args = parser.parse_args()

    path_to_dataset = f'{base_dir}/{args.path_to_dataset}'
    path_to_splits = f'{path_to_dataset}/splits'

    logging.info("Loading vocabulary into memory...")
    freqs = {}
    with open(f'{path_to_dataset}/vocab.txt', 'r') as f:
        for l in f:
            line = l.split()
            freqs[line[0]] = int(line[1])

    general_dict = load_english_dict(f'{base_project_dir}/dicts/eng')

    logging.info("Starting splitting...")
    transformed, nontransformed, possible_typos = get_splittings(freqs.keys(), freqs, general_dict, params)
    logging.info(f"Splitting done! Saving sata to '{path_to_split_folder}")
    path_to_split_folder = f'{path_to_splits}/1'
    while os.path.exists(path_to_split_folder):
        path_to_split_folder = f'{path_to_split_folder}1'

    os.makedirs(path_to_split_folder)

    with open(f'{path_to_split_folder}/params.json', 'w') as f:
        json.dump(params, f)

    print("\n################   Split  #####################")
    with open(f'{path_to_split_folder}/split.txt', 'w') as f:
        for word, tr in transformed.items():
            print(f'{word} --> {tr["subwords_set"]}')
            f.write(f'{word}|{" ".join(tr["subwords_set"])}\n')

    print("\n################ Non-split #####################")
    with open(f'{path_to_split_folder}/nonsplit.txt', 'w') as f:
        for word in nontransformed:
            print(f'{word}')
            f.write(f'{word}\n')

    print("\n################ Possible typos #####################")
    with open(f'{path_to_split_folder}/typos.txt', 'w') as f:
        for word in possible_typos:
            print(f'{word}')
            f.write(f'{word}\n')

    transformed_list = list(transformed.items())
    shuffle(transformed_list)
    shuffle(nontransformed)
    how_many_transformed = 1000
    how_many_nontransformed = 400
    with open(f'{path_to_split_folder}/sample.txt', 'w') as f:
        f.write("#####################  Split #####################\n")
        for w, tr in transformed_list[:how_many_transformed]:
            f.write(f'{w}|{" ".join(tr["subwords_set"])}\n')
        f.write("\n\n#####################  Non-split #####################\n")
        for w in nontransformed[:how_many_nontransformed]:
            f.write(f'{w}\n')
