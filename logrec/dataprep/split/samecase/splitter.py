import json
import logging
import os
from math import log
from multiprocessing.pool import Pool
from operator import itemgetter
from random import shuffle

from tqdm import tqdm

from logrec.util import io
from logrec.dataprep import base_project_dir

logger = logging.getLogger(__name__)


def get_next_combo(last_subwords_comb, max_subwords, non_ex_index=-1):
    if isinstance(last_subwords_comb, str):
        return [last_subwords_comb]
    # find last subword which length is more than 1
    start = len(last_subwords_comb)-1 if non_ex_index == -1 else non_ex_index
    while start >= 0 and (start+1 == max_subwords or len(last_subwords_comb[start]) == 1):
        start -= 1
    if start != -1:
        changed_part = get_next_combo(last_subwords_comb[start][-1] + "".join(last_subwords_comb[start+1:]),
                                      max_subwords - start - 1, -1)
        return last_subwords_comb[:start] + [last_subwords_comb[start][:-1]] + changed_part
    else:
        return None


def init_caches(common_cache_file, project_cache_file):
    cache = {}
    for file in (common_cache_file, project_cache_file):
        if os.path.exists(file):
            with open(file, 'r') as f:
                for line in f:
                    line = line if line[-1] != '\n' else line[:-1]
                    spl = line.split("|")
                    cache[spl[0]] = spl[1].split(" ")
    return cache


def init_cache(file):
    res=[]
    if os.path.exists(file):
        with open(file, 'r') as f:
            for line in f:
                res.append(line if line[-1] != '\n' else line[:-1])
    return res

def cache_comb_creator(split_cache, word):
    return [split_cache[word], [word]]


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


def calc_score(subwords_set, denum, denum_f, denum_l, freqs, general_dict):
    num = 0.0
    num_ls = []
    num_fs = []
    n = len(subwords_set)
    non_existant_word = None
    for ind, subword in enumerate(subwords_set):
        if subword in freqs:
            num_fs.append(ff(freqs[subword], subword in general_dict, n == 1, params))
            num_ls.append(ll(subword, params))
            num += num_fs[-1] * num_ls[-1]
        else:
            non_existant_word = ind
            break
    num = num * (1.0 / n ** params['lambda_'])
    if non_existant_word is None:
        result = num / denum
        return {
            'subwords_set': subwords_set,
            'num': num,
            'denum': denum,
            'results': result,
            'denum_f': denum_f,
            'denum_l': denum_l,
            'num_fs': num_fs,
            'num_ls': num_ls
        }
    else:
        return non_existant_word


def get_splitting(pp):
    word, freq, freqs, params, cached_combs, identity, general_dict = pp
    denum_f = ff(freq, word in general_dict, True, params)
    denum_l = ll(word, params)
    denum = denum_f * denum_l
    options = []
    pregenerated=True
    if cached_combs:
        combinations=cached_combs
    elif identity:
        combinations = [[word]]
    else:
        pregenerated=False
    if pregenerated:
        for subwords_set in combinations:
            score = calc_score(subwords_set, denum, denum_f, denum_l, freqs, general_dict)
            if score is not None:
                options.append(score)
    else:
        max_subwords = get_max_subwords(word)
        combo = get_next_combo(word, max_subwords, -1)
        while combo is not None:
            score = calc_score(combo, denum, denum_f, denum_l)
            if isinstance(score, dict):
                combo = get_next_combo(combo, max_subwords, -1)
                options.append(score)
            else:
                combo = get_next_combo(combo, max_subwords, score)

    options.sort(key=itemgetter('num'), reverse=True)
    for option in options[:5]:
        num_str = "avg(" + "+".join([f'{f:.2f}*{l:.2f}' for f, l in zip(option["num_fs"], option["num_ls"])]) + ")"
        logging.debug(
            f' {option["results"]:.2f}: {word} -> {option["subwords_set"]}:  {option["num"]:.2f}/{option["denum"]:.2f}='
            f'{num_str}/{option["denum_f"]:.2f}*{option["denum_l"]:.2f}')
    logging.debug("================================")
    if len(options) <= 0:
        raise AssertionError(f"No split options for: {word}. There should exist at least identity option")
    if options[0]["denum"] < typo_params['denum_error_likelihood_param'] \
            and options[0]["results"] < typo_params['error_likelihood_param'] \
            and len(word) >= typo_params['min_length_for_typo_detection']:
        return None, None, word
    if options[0]["results"] > 1.0 and len(options[0]["subwords_set"]) > 1:
        return (word, options[0]), None, None
    else:
        return None, word, None

def get_splittings(words_to_split, freqs, general_dict, non_eng_dicts, cache_files, params, general_cache_file):
    split_cache_file, nonsplit_cache_file, typo_candidates_cache_file = cache_files

    logging.info("Initializing caches...")
    split_cache = init_caches(split_cache_file, general_cache_file)
    nonsplit_cache = init_cache(nonsplit_cache_file)
    typo_candidates_cache = init_cache(typo_candidates_cache_file)

    logging.info("Starting splitting...")
    freqs = dict(sorted(freqs.items(), key=lambda x: len(x[0])))
    new_freqs = freqs.copy()
    transformed = {}
    nontransformed = []
    typo_candidates = []
    to_remove_from_new_freqs = []
    current_word_len = 0
    pp = []
    for ind, (word, freq) in enumerate(tqdm(freqs.items(), leave=False, total=len(freqs))):
        if word in words_to_split:
            # freqs should contain all the words from words_to_split, but the other way round is not guaranteed
            if len(word) > current_word_len:
                with Pool() as pool:
                    results = pool.map(get_splitting, pp)
                    pp = []
                for split_word, non_split_word, possible_typo in results:
                    if split_word is not None:
                        original_word, splitting = split_word
                        transformed[original_word] = splitting
                        to_remove_from_new_freqs.append(original_word)
                    elif non_split_word is not None:
                        nontransformed.append(non_split_word)
                    else:
                        typo_candidates.append(possible_typo)
                for to_remove in to_remove_from_new_freqs:
                    del (new_freqs[to_remove])
                del to_remove_from_new_freqs[:]
                current_word_len = len(word)

                dump_split(transformed, split_cache_file)
                dump_non_split(nontransformed, nonsplit_cache_file)
                dump_typo_candidates(typo_candidates, typo_candidates_cache_file)

                logging.info(f"Splitting words of length {current_word_len} (max word parts {get_max_subwords(word)})...")
            identity = False
            cached_combs = None
            if word in split_cache:
                cached_combs = cache_comb_creator(split_cache, word)
            elif (word in non_eng_dicts or word in general_dict) and len(word) >= 4:
                identity = True
            elif word in nonsplit_cache or word in typo_candidates_cache:
                identity = True
            pp.append((word, freq, new_freqs, params, cached_combs, identity, general_dict))

    return transformed, nontransformed, typo_candidates


def load_english_dict(path_to_dict_dir):
    english_dict = set()
    for file in os.listdir(path_to_dict_dir):
        with open(os.path.join(path_to_dict_dir, file), 'r') as f:
            for line in f:
                english_dict.add(line[:-1].lower())
    return english_dict


def load_non_english_dicts(path_to_dicts):
    dict = set()
    dict_files_names = [f for f in os.listdir(path_to_dicts)]
    for file in dict_files_names:
        with open(os.path.join(path_to_dicts, file)) as f:
            for l in f:
                dict.add(l[:-1] if l[-1] == '\n' else l)
    return dict


def dump_split(what, where):
    with open(where, 'w') as f:
        for word, tr in what.items():
            f.write(f'{word}|{" ".join(tr["subwords_set"])}\n')

def dump_non_split(what, where):
    with open(where, 'w') as f:
        for word in what:
            f.write(f'{word}\n')

def dump_typo_candidates(what, where):
    with open(where, 'w') as f:
        for word in what:
            f.write(f'{word}\n')

def generate_sample(transformed, nontransformed, nn, where):
    transformed_list = list(transformed.items())
    shuffle(transformed_list)
    shuffle(nontransformed)
    how_many_transformed = nn[0]
    how_many_nontransformed = nn[1]
    with open(where, 'w') as f:
        f.write("#####################  Split #####################\n")
        for w, tr in transformed_list[:how_many_transformed]:
            f.write(f'{w}|{" ".join(tr["subwords_set"])}\n')
        f.write("\n\n#####################  Non-split #####################\n")
        for w in nontransformed[:how_many_nontransformed]:
            f.write(f'{w}\n')


def run():
    path_to_splits = os.path.join(base_project_dir, 'splits')
    vocab_file = os.path.join(base_project_dir, 'vocab')

    logging.info(f"Loading vocabulary into memory from {vocab_file} ...")
    freqs = io.read_dict_from_2_columns(vocab_file)

    logging.info("Loading dictionaries")
    general_dict = load_english_dict(os.path.join(base_project_dir, 'dicts', 'eng'))
    non_eng_dicts = load_non_english_dicts(os.path.join(base_project_dir, 'dicts', 'non-eng'))

    path_to_split_folder = path_to_splits
    if not os.path.exists(path_to_splits):
        os.makedirs(path_to_split_folder)

    split_file = os.path.join(path_to_split_folder, 'splitting.txt')
    nonsplit_file = os.path.join(path_to_split_folder, 'nonsplit.txt')
    typo_candidates_file = os.path.join(path_to_split_folder, 'typo-candidates.txt')

    split_cache_file = f'{split_file}.cache'
    nonsplit_cache_file = f'{nonsplit_file}.cache'
    typo_candidates_cache_file = f'{typo_candidates_file}.cache'

    transformed, nontransformed, typo_candidates = get_splittings(freqs.keys(), freqs, general_dict, non_eng_dicts,
                                                                  (split_cache_file, nonsplit_cache_file, typo_candidates_cache_file),
                                                                  params,
                                                                  os.path.join(path_to_split_folder, 'split_cache.txt'))
    logging.info(f"Splitting done! Saving sata to '{path_to_splits}")

    with open(os.path.join(path_to_split_folder, 'params.json'), 'w') as f:
        json.dump({'params': params, 'typo_params': typo_params, 'max_subwords': max_subwords}, f)

    dump_split(transformed, split_file)
    dump_non_split(nontransformed, nonsplit_file)
    dump_typo_candidates(typo_candidates, typo_candidates_file)

    generate_sample(transformed, nontransformed, (1000, 4000), os.path.join(path_to_split_folder, 'sample.txt'))


if __name__ == '__main__':
    run()
