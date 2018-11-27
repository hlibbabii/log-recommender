import logging
import re
############   Multitoken list level    ###############3
import time

from logrec.dataprep import util
from logrec.dataprep.preprocessors.model.containers import ProcessableTokenContainer, SplitContainer
from logrec.dataprep.preprocessors.model.word import Word, WordStart, FullWord, SubWord, ParseableToken

logger = logging.getLogger(__name__)


class SplittingDict(metaclass=util.Singleton):
    def __init__(self, splitting_file_location):
        self.splitting_dict = {}
        start = time.time()
        with open(splitting_file_location, 'r') as f:
            for ln in f:
                word, splitting = ln.split("|")
                self.splitting_dict[word] = splitting.split()
        logger.info(f"Splitting dictionary is build in {time.time()-start} s")


def get_splitting_dictionary(splitting_file_location):
    return SplittingDict(splitting_file_location).splitting_dict


def simple_split(token_list, context):
    return [simple_split_token(identifier) for identifier in token_list]

#############  Token Level ################

def simple_split_token(token):
    if isinstance(token, ParseableToken):
        parts = [m[0] for m in
                 re.finditer('(_+$)|(_*(?:[0-9]+|[^A-Z0-9_]+|[A-Z][^A-Z0-9_]+|(?:[A-Z]+(?![^A-Z0-9_]))))', str(token))]
        if len(parts) > 1:
            processable_tokens = [SubWord.of(p) for p in parts]
            return SplitContainer(processable_tokens)
        else:
            return FullWord.of(parts[0])
    elif isinstance(token, ProcessableTokenContainer):
        return type(token)([simple_split_token(subtoken) for subtoken in token.get_subtokens()])
    else:
        return token

