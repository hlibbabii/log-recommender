from logrec.config.model import LMLRConfig, Data, Arch, RegFn, Droupouts
from logrec.properties import DEFAULT_DATASET

data = Data(
    dataset=DEFAULT_DATASET,
    repr='10411',
    percent=5,
    start_from=0,
    backwards=False
)

arch = Arch(
    bidir=False,
    qrnn=False,
    bs=32,
    validation_bs=16,
    bptt=990,
    em_sz=150,  # size of each embedding vector
    nh=300,  # number of hidden activations per layer
    nl=3,  # number of layers
    adam_betas=[0.7, 0.99],
    clip=0.3,
    reg_fn=RegFn(alpha=2, beta=1),
    drop=Droupouts(outi=0.05, out=0.05, w=0.1, oute=0.02, outh=0.05, multiplier=1),
)

lm_lr_config = LMLRConfig(
    base_model=None,
    data=data,
    arch=arch
)
