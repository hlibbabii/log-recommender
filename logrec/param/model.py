from enum import Enum
from typing import Optional, List


class ContextSide(str, Enum):
    BEFORE: str = 'before'
    AFTER: str = 'after'
    BOTH: str = 'both'


class Pretraining(str, Enum):
    FULL: str = 'full'
    ONLY_ENCODER: str = 'only_encoder'

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


class LangmodelTraining(object):
    def __init__(self, metrics: List[str], lr: float, wds: float, cycle: Cycle, backwards: bool):
        self.metrics = metrics
        self.lr = lr
        self.wds = wds
        self.cycle = cycle
        self.backwards = backwards


class Stage(object):
    def __init__(self, freeze_to: int, cycle: Cycle):
        self.freeze_to = freeze_to
        self.cycle = cycle


class ClassifierTraining(object):
    def __init__(self, metrics: List[str], lrs: List[float], wds: float, stages: List[Stage]):
        self.metrics = metrics
        self.lrs = lrs
        self.wds = wds
        self.stages = stages


class Validation(object):
    def __init__(self, bs: int, metrics: List[str]):
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
    def __init__(self, bidir: bool, qrnn: bool, bs: int, bptt: int, em_sz: int, nh: int, nl: int, min_freq: int,
                 betas: List[float],
                 clip: float, reg_fn: RegFn, drop: Droupouts):
        self.bidir = bidir
        self.qrnn = qrnn
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
    def __init__(self, data: Data, base_model: Optional[str], arch: Arch,
                 langmodel_training: LangmodelTraining,
                 validation: Validation,
                 testing: Testing):
        self.data = data
        self.base_model = base_model
        self.arch = arch
        self.langmodel_training = langmodel_training
        self.validation = validation
        self.testing = testing

    @property
    def validation_bs(self):
        return self.validation.bs

    @property
    def langmodel_training_config(self):
        return LangmodelTrainingConfig(data=self.data,
                                       arch=self.arch,
                                       training=self.langmodel_training,
                                       base_model=self.base_model)


class LangModelLrLearningParams(object):
    def __init__(self, data: Data, base_model: Optional[str], arch: Arch):
        self.data = data
        self.base_model = base_model
        self.arch = arch

    @property
    def validation_bs(self):
        return self.arch.bs

    @property
    def langmodel_training_config(self):
        return LangmodelTrainingConfig(data=self.data,
                                       arch=self.arch,
                                       training=None,
                                       base_model=self.base_model)


class ClassifierTrainingParams(object):
    def __init__(self, classification_type: str, data: Data,
                 log_coverage_threshold: float, context_side: ContextSide, base_model: Optional[str],
                 pretraining: Optional[Pretraining], arch: Arch,
                 classifier_training: ClassifierTraining, validation: Validation,
                 testing: Testing):
        self.classification_type = classification_type
        self.data = data
        self.log_coverage_threshold = log_coverage_threshold
        self.context_side = context_side
        self.base_model = base_model
        self.pretraining = pretraining
        self.arch = arch
        self.classifier_training = classifier_training
        self.validation = validation
        self.testing = testing

    @property
    def classifier_training_config(self):
        return ClassifierTrainingConfig(classification_type=self.classification_type,
                                        data=self.data,
                                        log_coverage_threshold=self.log_coverage_threshold,
                                        context_side=self.context_side,
                                        arch=self.arch,
                                        training=self.classifier_training,
                                        base_model=self.base_model,
                                        pretraining=self.pretraining)


class LangmodelTrainingConfig(object):
    def __init__(self, data: Data, arch: Arch, training: Optional[LangmodelTraining], base_model: Optional[str]):
        self.data = data
        self.arch = arch
        self.training = training
        self.base_model = base_model


class ClassifierTrainingConfig(object):
    def __init__(self, classification_type: str, data: Data, log_coverage_threshold: float, context_side: ContextSide,
                 arch: Arch, training: ClassifierTraining, base_model: Optional[str],
                 pretraining: Optional[Pretraining]):
        self.classification_type = classification_type
        self.data = data
        self.log_coverage_threshold = log_coverage_threshold
        self.context_side = context_side
        self.arch = arch
        self.training = training
        self.base_model = base_model
        self.pretraining = pretraining
