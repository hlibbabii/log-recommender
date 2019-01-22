from logrec.properties import DEFAULT_DATASET
from logrec.param.model import Droupouts, RegFn, Cycle, Validation, Testing, Data, Arch, \
    ClassifierTrainingParams, ClassifierTraining, Stage, \
    Pretraining, ContextSide

data = Data(
    dataset=DEFAULT_DATASET,
    repr='10411',
    percent=100,
    start_from=0,
)

arch = Arch(
    bidir=False,
    qrnn=False,
    bs=16,
    bptt=10,
    em_sz=150,  # size of each embedding vector
    nh=300,  # number of hidden activations per layer
    nl=3,  # number of layers
    min_freq=0,
    betas=[0.7, 0.99],
    clip=0.3,
    reg_fn=RegFn(alpha=2, beta=1),
    drop=Droupouts(outi=0.05, out=0.05, w=0.1, oute=0.02, outh=0.05),
)

base_lr = 1.1e-3
factor = 2.6

classifier_training_param = ClassifierTrainingParams(
    classification_type='level',
    data=data,
    log_coverage_threshold=5.0,
    context_side=ContextSide.BEFORE,
    base_model='test1/1proj__100_baseline_extratrained_-_100_baseline',
    pretraining=Pretraining.FULL,
    arch=arch,
    classifier_training=ClassifierTraining(
        metrics=['accuracy', 'mrr'],
        lrs=[base_lr / factor ** 4,
             base_lr / factor ** 3,
             base_lr / factor ** 2.5,
             base_lr / factor,
             base_lr
             ],
        wds=1.1e-6,
        stages=[
            # Stage(-1, Cycle(len=0, n=1, mult=1)),
            Stage(0, Cycle(len=1, n=1, mult=2))
        ]

    ),
    validation=Validation(
        bs=64,
        metrics=['accuracy', 'mrr']
    ),
    testing=Testing(
        how_many_words=2000,
        starting_words='<comment> public static class'
    ),
)
