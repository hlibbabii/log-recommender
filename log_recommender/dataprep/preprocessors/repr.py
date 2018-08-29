from dataprep.preprocessors.model.split import NonDelimiterSplitContainer
from dataprep.preprocessors.preprocessing_types import token_to_preprocessing_type_level_dict, always_repr, recursive


def to_repr(preprocessing_params, token_list):
    types_to_be_repr_dict = {k:preprocessing_params[v] for (k, v) in token_to_preprocessing_type_level_dict.items()
                             if v in preprocessing_params}
    repr_list = to_repr_list(types_to_be_repr_dict, token_list)
    return repr_list


def to_repr_list(types_to_be_repr_dict, token_list):
    repr_res = []
    for token in token_list:
        repr_token = to_repr_token(types_to_be_repr_dict, token)
        repr_res.extend(repr_token if isinstance(repr_token, list) else [repr_token])
    return repr_res


def to_repr_token(types_to_be_repr_dict, token):
    clazz = type(token)
    if clazz in always_repr:
        return token.to_repr()
    elif clazz in types_to_be_repr_dict:
        if types_to_be_repr_dict[clazz]:
            repr = token.preprocessed_repr()
        else:
            repr = token.non_preprocessed_repr()
        if clazz in recursive and isinstance(repr, list):
            return to_repr_list(types_to_be_repr_dict, repr)
        elif clazz in recursive:
            return to_repr_token(types_to_be_repr_dict, repr)
        else:
            return repr
    elif clazz in recursive:
        repr_list = to_repr_list(types_to_be_repr_dict, token.get_subtokens())
        if isinstance(token, NonDelimiterSplitContainer):
            return clazz(repr_list, token.is_capitalized())
        else:
            return clazz(repr_list)
    else:
        return token
