import multiprocessing
import threading


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


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class AtomicInteger(object):
    def __init__(self, v=0):
        self._lock = threading.Lock()
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
