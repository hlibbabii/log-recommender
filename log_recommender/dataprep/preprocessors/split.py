import re

from dataprep.preprocessors import placeholders
from dataprep.preprocessors.util import add_between_elements


############   Multitoken list level    ###############3

def camel_case(context_line):
    return [item for identifier in context_line
            for item in camel_case_split(identifier, add_separator=True)]


def underscore(context_line):
    return [item for identifier in context_line
            for item in underscore_split(identifier, add_separator=True)]


def with_numbers(line):
    return [item for identifier in line
            for item in split_with_numbers(identifier, add_separator=True)]


#############  Token Level ################

def camel_case_split(identifier, add_separator=False):
    if identifier == '\n': #TODO XXX
        return [identifier]
    matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', identifier)
    parts = [m.group(0).lower() for m in matches]
    return add_between_elements(parts, placeholders['camel_case_separator']) if add_separator else parts


def split_with_numbers(identifier, add_separator=False):
    parts = list(filter(None, re.split('(?<=[a-zA-Z0-9])?([0-9])(?=[a-zA-Z0-9]+|$)', identifier)))
    return add_between_elements(parts, placeholders['camel_case_separator']) if add_separator else parts


def underscore_split(identifier, add_separator=False):
    #TODO it creates empty element if the identifier starts or ends with underscore
    parts = identifier.split("_")
    parts_with_separators = add_between_elements(parts,
                                                 placeholders['underscore_separator']) if add_separator else parts
    if parts_with_separators[0] == '':
        del (parts_with_separators[0])
    if parts_with_separators[-1] == '':
        del (parts_with_separators[-1])
    return parts_with_separators