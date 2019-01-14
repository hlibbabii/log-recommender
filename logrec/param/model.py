from typing import Optional, List


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
    def __init__(self, device: int, data: Data, base_model: Optional[str], arch: Arch,
                 langmodel_training: LangmodelTraining,
                 validation: Validation,
                 testing: Testing):
        self.device = device
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
        return LangmodelTrainingConfig(arch=self.arch,
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
        return LangmodelTrainingConfig(arch=self.arch,
                                       training=None,
                                       base_model=self.base_model)


class ClassifierTrainingParams(object):
    def __init__(self, data: Data, base_model: Optional[str],
                 pretrained_model: Optional[str], arch: Arch,
                 langmodel_training: LangmodelTraining,
                 classifier_training: ClassifierTraining, validation: Validation,
                 testing: Testing, threshold: float, classification_type: str):
        self.data = data
        self.base_model = base_model
        self.pretrained_model = pretrained_model
        self.arch = arch
        self.langmodel_training = langmodel_training
        self.classifier_training = classifier_training
        self.validation = validation
        self.testing = testing
        self.threshold = threshold
        self.classification_type = classification_type

    @property
    def classifier_training_config(self):
        return ClassifierTrainingConfig(arch=self.arch,
                                        training=self.classifier_training,
                                        base_model=self.base_model)


class LangmodelTrainingConfig(object):
    def __init__(self, arch: Arch, training: Optional[LangmodelTraining], base_model: Optional[str]):
        self.arch = arch
        self.training = training
        self.base_model = base_model


class ClassifierTrainingConfig(object):
    def __init__(self, arch: Arch, training: ClassifierTraining, base_model: Optional[str]):
        self.arch = arch
        self.training = training
        self.base_model = base_model
