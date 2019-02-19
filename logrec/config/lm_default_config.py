from logrec.properties import DEFAULT_DATASET
from logrec.config.model import Droupouts, RegFn, Cycle, LMTraining, LMTesting, Data, Arch, LMConfig, Cache

data = Data(
    dataset=DEFAULT_DATASET,
    repr='',
    percent=0.,
    start_from=0,
    backwards=False
)

arch = Arch(
    bidir=False,
    qrnn=False,
    bs=64,
    validation_bs=32,
    bptt=290,
    em_sz=300,  # size of each embedding vector
    nh=650,  # number of hidden activations per layer
    nl=3,  # number of layers
    adam_betas=[0.7, 0.99],
    clip=0.3,
    reg_fn=RegFn(alpha=2, beta=1),
    drop=Droupouts(outi=0.05, out=0.05, w=0.1, oute=0.02, outh=0.05, multiplier=1.0),
)

lm_training = LMTraining(
    lr=1e-3,
    wds=1e-6,
    cycle=Cycle(n=1, len=1, mult=1),
    early_stop=True
)

lm_config = LMConfig(
    base_model=None,
    data=data,
    arch=arch,
    training=lm_training,
    metrics=['accuracy', 'mrr'],
    cache=Cache(theta=0.4, lambdah=0.2, window=0),
    use_subword_aware_metrics=False,
    testing=LMTesting(
        n_words_to_generate=2000,
        starting_words='class'
    )
)

