from enum import Enum
from typing import Optional, List

CONFIG_VERSION = 1


class Droupouts(object):
    def __init__(self, multiplier: float,
                 oute: float,
                 outi: float,
                 outh: float,
                 w: float,
                 out: float):
        self.multiplier = multiplier
        self.oute = oute
        self.outi = outi
        self.outh = outh
        self.w = w
        self.out = out


class RegFn(object):
    def __init__(self, alpha: float, beta: float):
        self.alpha = alpha
        self.beta = beta


class Cycle(object):
    def __init__(self, n: int, len: int, mult: int):
        self.n = n
        self.len = len
        self.mult = mult


class Data(object):
    def __init__(self, dataset: str, repr: str, percent: float,
                 start_from: float, backwards: bool):
        self.dataset = dataset
        self.repr = repr
        self.percent = percent
        self.start_from = start_from
        self.backwards = backwards


class Arch(object):
    def __init__(self, bidir: bool, qrnn: bool, bs: int, validation_bs: int,
                 bptt: int, em_sz: int, nh: int, nl: int, adam_betas: List[float],
                 clip: float, reg_fn: RegFn, drop: Droupouts):
        self.bidir = bidir
        self.qrnn = qrnn
        self.bs = bs
        self.validation_bs = validation_bs
        self.bptt = bptt
        self.em_sz = em_sz
        self.nh = nh
        self.nl = nl
        self.adam_betas = adam_betas
        self.clip = clip
        self.reg_fn = reg_fn
        self.drop = drop


class Cache(object):
    def __init__(self, theta: float, lambdah: float, window: int):
        self.theta = theta
        self.lambdah = lambdah
        self.window = window

############   LM LR specific    ##########################


class LMLRConfig(object):
    def __init__(self, data: Data, base_model: Optional[str], arch: Arch):
        self.data = data
        self.base_model = base_model
        self.arch = arch

    @property
    def training_config(self):
        return LMTrainingConfig(base_model=self.base_model,
                                data=self.data,
                                arch=self.arch,
                                training=None)


############   Lang Model specific      ###################


class LMTraining(object):
    def __init__(self, lr: float, wds: float, cycle: Cycle, early_stop: bool):
        self.lr = lr
        self.wds = wds
        self.cycle = cycle
        self.early_stop = early_stop


class LMTesting(object):
    def __init__(self, n_words_to_generate: int, starting_words: str):
        self.n_words_to_generate = n_words_to_generate
        self.starting_words = starting_words


class LMTrainingConfig(object):

    def __init__(self, base_model: Optional[str], data: Data, arch: Arch,
                 training: Optional[LMTraining], config_version: str = CONFIG_VERSION):
        self.base_model = base_model
        self.data = data
        self.arch = arch
        self.training = training
        self.config_version = config_version

        if config_version != CONFIG_VERSION:
            raise TypeError(f'Trying to deserealize '
                            f'CONFIG_VERSION {config_version} '
                            f'to CONFIG_VERSION {CONFIG_VERSION} object')


class LMConfig(object):
    def __init__(self, base_model: Optional[str], data: Data, arch: Arch,
                 training: LMTraining,
                 metrics: List[str],
                 cache: Optional[Cache],
                 use_subword_aware_metrics: bool,
                 testing: LMTesting):
        self.base_model = base_model
        self.data = data
        self.arch = arch
        self.training = training
        self.metrics = metrics
        self.cache = cache
        self.use_subword_aware_metrics = use_subword_aware_metrics
        self.testing = testing

    @property
    def training_config(self):
        return LMTrainingConfig(base_model=self.base_model,
                                data=self.data,
                                arch=self.arch,
                                training=self.training)


#############  Classifier specific    #############################


class PretrainingType(str, Enum):
    FULL: str = 'full'
    ONLY_ENCODER: str = 'only_encoder'


class ClassificationType(str, Enum):
    LOCATION: str = 'location'
    LEVEL: str = 'level'
    LEVEL_BINARY = 'level_binary'


class Stage(object):
    def __init__(self, freeze_to: int, cycle: Cycle):
        self.freeze_to = freeze_to
        self.cycle = cycle


class LRS(object):
    def __init__(self, base_lr: float, factor: float, multipliers: List[float]):
        self.base_lr = base_lr
        self.factor = factor
        self.multipliers = multipliers


class ClassifierTraining(object):
    def __init__(self, lrs: LRS, wds: float, stages: List[Stage], early_stop: bool):
        self.lrs = lrs
        self.wds = wds
        self.stages = stages
        self.early_stop = early_stop


class ClassifierTrainingConfig(object):

    def __init__(self, base_model: Optional[str],
                 pretraining: Optional[PretrainingType],
                 data: Data, arch: Arch, classification_type: str,
                 min_log_coverage_percent: float,
                 training: ClassifierTraining, config_version: int = CONFIG_VERSION):
        self.base_model = base_model
        self.pretraining = pretraining
        self.data = data
        self.arch = arch
        self.classification_type = classification_type
        self.min_log_coverage_percent = min_log_coverage_percent
        self.training = training
        self.config_version = config_version

        if config_version != CONFIG_VERSION:
            raise TypeError(f'Trying to deserealize '
                            f'CONFIG_VERSION {config_version} '
                            f'to CONFIG_VERSION {CONFIG_VERSION} object')


class ClassifierTesting(object):
    def __init__(self, n_samples: int):
        self.n_samples = n_samples


class ClassifierConfig(object):
    def __init__(self, base_model: Optional[str],
                 pretraining_type: Optional[PretrainingType],
                 data: Data, arch: Arch, classification_type: str,
                 min_log_coverage_percent: float,
                 training: ClassifierTraining, metrics: List[str],
                 testing: ClassifierTesting):
        self.base_model = base_model
        self.pretraining_type = pretraining_type
        self.data = data
        self.arch = arch
        self.classification_type = classification_type
        self.min_log_coverage_percent = min_log_coverage_percent
        self.training = training
        self.metrics = metrics
        self.testing = testing

    @property
    def training_config(self):
        return ClassifierTrainingConfig(base_model=self.base_model,
                                        pretraining=self.pretraining_type,
                                        data=self.data,
                                        arch=self.arch,
                                        classification_type=self.classification_type,
                                        min_log_coverage_percent=self.min_log_coverage_percent,
                                        training=self.training)
