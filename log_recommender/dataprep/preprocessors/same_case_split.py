from dataprep.preprocessors import placeholders
from dataprep.preprocessors.util import add_between_elements

############   Multitoken list level    ###############3

def split(splitting_file_location, line):
    splitting_dict = {}
    with open(splitting_file_location, 'r') as f:
        for ln in f:
            word, splitting = ln.split("|")
            splitting_dict[word] = splitting.split()

    return [item for identifier in line
            for item in split_same_case(identifier, splitting_dict, add_separator=True)]

#############  Token Level ################

def split_same_case(identifier, splitting_dict, add_separator=False):
    if identifier in splitting_dict:
        parts = splitting_dict[identifier]
    else:
        parts = [identifier]
    return add_between_elements(parts, placeholders['same_case_separator']) if add_separator else parts