import multiprocessing
from typing import Dict, Tuple, List


def insert_separators(subwords, separator):
    return [s for subword in subwords for s in (subword, separator)][:-1]

def create_regex_from_token_list(token_list):
    m = list(map(lambda x:
             x.replace('\\', '\\\\')
                 .replace("^", "\\^")
                 .replace("+", "\+")
                 .replace("|", "\|")
                 .replace("*", "\*")
                 .replace("[", "\[")
                 .replace("]", "\]")
                 .replace("-", "\-")
                 .replace('"', '\\"')
                 .replace('?', "\?")
                 .replace('(', "\(")
                 .replace(')', "\)")
                 .replace(".", "\.")
                 .replace("$", "\$")
                 , token_list))
    return "(" + "|".join(
        m
    ) +")"


def merge_dicts_(dict1, dict2) -> Tuple[Dict, List]:
    '''
    this method returns modified dict1! and new words are added to the dictionary
    :param dict1:
    :param dict2:
    :return:
    '''
    new_words = []
    for k, v in dict2.items():
        if k not in dict1:
            dict1[k] = v
            new_words.append(k)
        else:
            dict1[k] = dict1[k] + v
    return dict1, new_words


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class AtomicInteger(object):
    def __init__(self, v=0):
        self._lock = multiprocessing.Lock()
        self._queue = multiprocessing.Queue()
        for i in range(v):
            self._queue.put(1)

    def inc(self):
        with self._lock:
            self._queue.put(1)
            return self._queue.qsize()

    def dec(self):
        with self._lock:
            self._queue.get()
            return self._queue.qsize()

    def compare_and_dec(self, val):
        with self._lock:
            result = self._queue.qsize() == val
            self._queue.get()
            return result

    def get_and_dec(self):
        with self._lock:
            result = self._queue.qsize()
            self._queue.get()
            return result

    @property
    def value(self):
        with self._lock:
            return self._queue.qsize()

    @value.setter
    def value(self, v):
        with self._lock:
            self._queue = multiprocessing.Queue()
            for i in range(v):
                self._queue.put(1)


def dump_dict_into_2_columns(dct, file, val_type=str, delim='\t', append=False):
    with open(file, 'w+' if append else 'w') as f:
        lst = dct.items() if isinstance(dct, dict) else dct
        for word, freq in lst:
            value = ' '.join(freq) if val_type == list else str(freq)
            f.write(f'{str(word)}{delim}{value}\n')


def read_dict_from_2_columns(file, val_type=str, delim='\t'):
    words = {}
    with open(file, 'r') as f:
        for line in f:
            line = line[:-1] if line[-1] else line
            splits = line.split(delim)
            if val_type == list:
                second_column = splits[1].split(' ')
            else:
                try:
                    second_column = int(splits[1])
                except:
                    second_column = splits[1]
            words[splits[0]] = second_column
    return words


def read_list(file):
    res = []
    with open(file, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            splits = line.split(' ')
            res.append(splits if len(splits) > 1 else splits[0])
    return res


def dump_list(lst, file):
    with open(file, 'w') as f:
        for elm in lst:
            if isinstance(elm, list) or isinstance(elm, tuple):
                f.write(f"{' '.join(elm)}\n")
            else:
                f.write(f"{elm}\n")
