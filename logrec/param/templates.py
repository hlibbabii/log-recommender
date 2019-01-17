from logrec.properties import DEFAULT_DATASET
from logrec.param.model import Droupouts, RegFn, Cycle, LangmodelTraining, Validation, Testing, Data, Arch, \
    LangModelTrainingParams, LangModelLrLearningParams, ClassifierTrainingParams, ClassifierTraining, Stage

data = Data(
    dataset=DEFAULT_DATASET,
    repr='101011',
    percent=1,
    start_from=0,
)

arch = Arch(
    bidir=False,
    qrnn=False,
    bs=16,
    bptt=1000,
    em_sz=150,  # size of each embedding vector
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

langmodel_training = LangmodelTraining(
    metrics=['accuracy', 'mrr'],
    lr=1.1e-3,
    wds=1e-6,
    cycle=Cycle(n=1, len=1, mult=2),
    backwards=True
)

langmodel_training_params = LangModelTrainingParams(
    data=data,
    base_model=None,
    arch=arch,
    langmodel_training=langmodel_training,
    validation=Validation(
        bs=64,
        metrics=['accuracy', 'mrr']
    ),
    testing=Testing(
        how_many_words=2000,
        starting_words='''
`c `C n o t `c s u p p or te d `c e x ce p tion w` ( " `c `C get `c `Cs x a `c re s o ur ce w` `c n o t w` `c s u p p or te d w` `c n o t w` `c s u p p or te d w` " ) ; } /* * * `c `C get s w` the `c m e t a d a t a w` `c in f or m a tion w` `c f or w` `c th is w` `c con n ec tion w` \' s `c u n d e r l y i n g w` `c `Cs e i s w` `c re s o ur ce w` `c m an a g er w` `c in st an ce w` . * * @ return `c `C m an a ge d `c con n ec tion `c m e t a `c d a t a w` `c in st an ce w` * @ `c th ro w s w` `c `C re s o ur ce `c e x ce p tion w` `c g e n e r i c w` `c e x ce p tion w` if `c o per a tion w` `c f a i l s w` */ `c p u b li c w` `c `C m an a ge d `c con n ec tion `c m e t a `c d a t a w` `c get `c m e t a `c d a t a w` ( ) `c th ro w s w` `c `C re s o ur ce `c e x ce p tion w` {        
'''
    )
)

base_lr = 1e-3
factor = 2.6

classifier_training_param = ClassifierTrainingParams(
    classification_type='location',
    data=data,
    log_coverage_threshold=5.0,
    context_side='before',
    pretrained_model='1_baseline',
    base_model=None,
    arch=arch,
    langmodel_training=langmodel_training,
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
            Stage(0, Cycle(len=0, n=0, mult=2))
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
