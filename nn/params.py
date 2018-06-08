from torchtext import data

PATH='../nn-data'

# bs=32
bs=8
bptt=40
em_sz = 70  # size of each embedding vector
nh = 100     # number of hidden activations per layer
nl = 3       # number of layers

TEXT = data.Field()
LEVEL_LABEL = data.Field(sequential=False)

pretrained_lang_model_name='no_replaced_identifier_split'