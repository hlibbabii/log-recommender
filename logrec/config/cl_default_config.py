from logrec.properties import DEFAULT_DATASET
from logrec.config.model import Droupouts, RegFn, Cycle, Data, Arch, \
    ClassifierConfig, ClassifierTraining, Stage, \
    PretrainingType, LRS, ClassificationType, ClassifierTesting

data = Data(
    dataset='nodup_en_only',
    repr='324101',
    percent=100,
    start_from=0,
    backwards=False
)

arch = Arch(
    bidir=False,
    qrnn=False,
    bs=64,
    validation_bs=32,
    bptt=990,
    em_sz=300,  # size of each embedding vector
    nh=650,  # number of hidden activations per layer
    nl=3,  # number of layers
    adam_betas=[0.7, 0.99],
    clip=25.,
    reg_fn=RegFn(alpha=2, beta=1),
    drop=Droupouts(outi=0.05, out=0.05, w=0.1, oute=0.02, outh=0.05, multiplier=1.0),
)

classifier_config = ClassifierConfig(
    base_model='100_baseline_extratrained_extratrained',
    pretraining_type=PretrainingType.ONLY_ENCODER,
    data=data,
    arch=arch,
    classification_type=ClassificationType.LOCATION,
    min_log_coverage_percent=5.0,
    training=ClassifierTraining(
        lrs=LRS(
            base_lr=1e-3,
            factor=2.6,
            multipliers=[4, 3, 2.5, 1, 0]
        ),
        wds=1e-6,
        stages=[
            # Stage(-1, Cycle(len=0, n=1, mult=1)),
            # Stage(-2, Cycle(len=0, n=1, mult=1)),
            Stage(0, Cycle(len=1, n=1, mult=2))
        ],
        early_stop=True

    ),
    metrics=['accuracy', 'mrr'],
    testing=ClassifierTesting(n_samples=20)
)
