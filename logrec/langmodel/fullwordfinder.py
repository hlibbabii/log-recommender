from logrec.dataprep.preprocessors.model.placeholders import placeholders

subword_separators_boundaries = [
    placeholders['camel_case_separator'],
    placeholders['underscore_separator']]

subword_separators_separators = [placeholders['same_case_separator']] \
                                + subword_separators_boundaries

capitals = [placeholders['capital'], placeholders['capitals']]


def get_subword(seq, ps, current_target, current_p, text_files):
    return current_target, current_p, None, None
    

def get_curr_seq(seq, ps, current_target, current_p, text_field):
    if not seq:  # only the beginning:
        return None, None, [current_target], [current_p]

    last_seq_word = text_field.vocab.itos[seq[-1][0]]
    current_target_word = text_field.vocab.itos[current_target[0]]

    if current_target_word in capitals and last_seq_word in subword_separators_separators:
        return None, None, seq + [current_target], ps + [current_p]

    if (current_target_word not in subword_separators_separators) \
            and (last_seq_word not in subword_separators_separators + capitals):
        return seq, ps, [current_target], [current_p]
    elif (current_target_word in subword_separators_separators) \
            != (last_seq_word in subword_separators_separators + capitals):
        # ongoing split word
        return None, None, seq + [current_target], ps + [current_p]
    else:
        # current_target in separators and seq[-1] not separators
        raise AssertionError(f"Two separators in a row are not allowed: {last_seq_word}, {current_target_word}")


def get_curr_seq_new(seq, ps, current_target, current_p, text_field):
    current_target_word = text_field.vocab.itos[current_target[0]]
    first_of_seq = text_field.vocab.itos[seq[0][0]] if seq else None
    if current_target_word in capitals:
        return None, None, seq + [current_target], ps + [current_p]

    if not seq:
        if current_target_word in [placeholders['camel_case_separator']] + capitals:
            return None, None, [current_target], [current_p]
        elif current_target_word == placeholders['split_words_end']:
            raise AssertionError(f"Split end separator without split start")
        else:
            return [current_target], [current_p], [], []
    elif first_of_seq != placeholders['camel_case_separator'] \
            or current_target_word == placeholders['split_words_end']:
        return seq + [current_target], ps + [current_p], [], []
    else:
        return [], [], seq + [current_target], ps + [current_p]
