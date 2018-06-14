from torchtext import data

PATH='../nn-data'

# bs=32
bs=64
bptt=70
em_sz = 300  # size of each embedding vector
nh = 400     # number of hidden activations per layer
nl = 3       # number of layers

TEXT = data.Field()
LEVEL_LABEL = data.Field(sequential=False)

pretrained_lang_model_name='devanbu_no_replaced_identifier_split'