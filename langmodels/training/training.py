import sys

import dataprep.api.corpus as api
from dataprep.api.corpus import PreprocessedCorpus
from fastai.text import Vocab, TextList, NumericalizeProcessor, OpenFileProcessor

if __name__ == '__main__':
    prep_corpus:PreprocessedCorpus = api.bpe('/home/hlib/dev/yahtzee', '10k', calc_vocab=True)
    vocab = Vocab(list(prep_corpus.load_vocab().keys()))
    text_list = TextList.from_folder(prep_corpus.path_to_prep_dataset, vocab=vocab, extensions=['.prep'],
                                  processor=[OpenFileProcessor(),
                                             NumericalizeProcessor(vocab=vocab, max_vocab=sys.maxsize, min_freq=0)])\
        .split_by_rand_pct()\
        .label_for_lm()\
        .databunch()
    print(text_list)
