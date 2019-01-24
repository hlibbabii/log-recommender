from logrec.properties import DEFAULT_DATASET
from logrec.config.model import Droupouts, RegFn, Cycle, Data, Arch, \
    ClassifierConfig, ClassifierTraining, Stage, \
    PretrainingType, LRS, ClassificationType, ClassifierTesting

data = Data(
    dataset=DEFAULT_DATASET,
    repr='10411',
    percent=100,
    start_from=0,
    backwards=False
)

arch = Arch(
    bidir=False,
    qrnn=False,
    bs=32,
    validation_bs=32,
    bptt=990,
    em_sz=150,  # size of each embedding vector
    nh=300,  # number of hidden activations per layer
    nl=3,  # number of layers
    adam_betas=[0.7, 0.99],
    clip=25.,
    reg_fn=RegFn(alpha=2, beta=1),
    drop=Droupouts(outi=0.05, out=0.05, w=0.1, oute=0.02, outh=0.05, multiplier=1.0),
)

classifier_config = ClassifierConfig(
    base_model=None,
    pretraining_type=None,
    data=data,
    arch=arch,
    classification_type=ClassificationType.LOCATION,
    min_log_coverage_percent=1.0,
    training=ClassifierTraining(
        lrs=LRS(
            base_lr=1e-3,
            factor=1.0,
            multipliers=[4, 3, 2.5, 1, 0]
        ),
        wds=1e-6,
        stages=[
            # Stage(-1, Cycle(len=0, n=1, mult=1)),
            # Stage(-2, Cycle(len=0, n=1, mult=1)),
            Stage(0, Cycle(len=4, n=1, mult=2))
        ],
        early_stop=True

    ),
    metrics=['accuracy', 'mrr'],
    testing=ClassifierTesting(n_samples=200)
)
