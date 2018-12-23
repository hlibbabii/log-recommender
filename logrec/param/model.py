from typing import Sequence, Optional


class Droupouts(object):
    def __init__(self, outi: float, out: float, w: float, oute: float, outh: float):
        self.outi = outi
        self.out = out
        self.w = w
        self.oute = oute
        self.outh = outh


class RegFn(object):
    def __init__(self, alpha: float, beta: float):
        self.alpha = alpha
        self.beta = beta


class Cycle(object):
    def __init__(self, n: int, len: int, mult: int):
        self.n = n
        self.len = len
        self.mult = mult


class Training(object):
    def __init__(self, cycle: Cycle, metrics: Sequence[str], lr: float, wds: float):
        self.cycle = cycle
        self.metrics = metrics
        self.lr = lr
        self.wds = wds


class Validation(object):
    def __init__(self, bs: int, metrics: Sequence[str]):
        self.bs = bs
        self.metrics = metrics


class Testing(object):
    def __init__(self, how_many_words: int, starting_words: str):
        self.how_many_words = how_many_words
        self.starting_words = starting_words


class Data(object):
    def __init__(self, dataset: str, repr: str, percent: float, start_from: float):
        self.dataset = dataset
        self.repr = repr
        self.percent = percent
        self.start_from = start_from


class Arch(object):
    def __init__(self, bidir: bool, bs: int, bptt: int, em_sz: int, nh: int, nl: int, min_freq: int,
                 betas: Sequence[float],
                 clip: float, reg_fn: RegFn, drop: Droupouts):
        self.bidir = bidir
        self.bs = bs
        self.bptt = bptt
        self.em_sz = em_sz
        self.nh = nh
        self.nl = nl
        self.min_freq = min_freq
        self.betas = betas
        self.clip = clip
        self.reg_fn = reg_fn
        self.drop = drop


class LangModelTrainingParams(object):
    def __init__(self, data: Data, base_model: Optional[str], arch: Arch, training: Training, validation: Validation,
                 testing: Testing):
        self.data = data
        self.base_model = base_model
        self.arch = arch
        self.training = training
        self.validation = validation
        self.testing = testing


class LangModelLrLearningParams(object):
    def __init__(self, data: Data, base_model: Optional[str], arch: Arch):
        self.data = data
        self.base_model = base_model
        self.arch = arch


class ClassifierTrainingParams(object):
    def __init__(self, data: Data, base_model: Optional[str], arch: Arch, training: Training, validation: Validation,
                 testing: Testing, threshold: float, classification_type: str):
        self.data = data
        self.base_model = base_model
        self.arch = arch
        self.training = training
        self.validation = validation
        self.testing = testing
        self.threshold = threshold
        self.classification_type = classification_type
