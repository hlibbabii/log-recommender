from logrec.local_properties import DEFAULT_DATASET
from logrec.param.model import Droupouts, RegFn, Cycle, Training, Validation, Testing, Data, Arch, \
    LangModelTrainingParams, LangModelLrLearningParams, ClassifierTrainingParams

data = Data(
    dataset=DEFAULT_DATASET,
    repr='104111',
    percent=1,
    start_from=0,
)

arch = Arch(
    bidir=False,
    bs=16,
    bptt=10,
    em_sz=300,  # size of each embedding vector
    nh=300,  # number of hidden activations per layer
    nl=3,  # number of layers
    min_freq=0,
    betas=[0.7, 0.99],
    clip=0.3,
    reg_fn=RegFn(alpha=2, beta=1),
    drop=Droupouts(outi=0.05, out=0.05, w=0.1, oute=0.02, outh=0.05),
)

langmodel_lr_learning_params = LangModelLrLearningParams(
    data=data,
    base_model=None,
    arch=arch
)

langmodel_training_params = LangModelTrainingParams(
    data=data,
    base_model=None,
    arch=arch,
    training=Training(
        cycle=Cycle(n=1, len=1, mult=2),
        metrics=['accuracy', 'mrr'],
        lr=1e-3,
        wds=1e-6,
    ),
    validation=Validation(
        bs=64,
        metrics=['accuracy', 'mrr']
    ),
    testing=Testing(
        how_many_words=2000,
        starting_words='<comment> public static class'
    )
)

classifier_training_param = ClassifierTrainingParams(
    data=data,
    base_model='1_baseline',
    arch=arch,
    training=Training(
        cycle=Cycle(n=1, len=1, mult=2),
        metrics=['accuracy', 'mrr'],
        lr=1e-3,
        wds=1e-6,
    ),
    validation=Validation(
        bs=64,
        metrics=['accuracy', 'mrr']
    ),
    testing=Testing(
        how_many_words=2000,
        starting_words='<comment> public static class'
    ),
    threshold=5.0,
    classification_type="location"
)
