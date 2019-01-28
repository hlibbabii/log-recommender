def dump_dict_into_2_columns(dct, file, val_type=str, delim='\t', append=False):
    with open(file, 'w+' if append else 'w') as f:
        lst = dct.items() if isinstance(dct, dict) else dct
        for word, freq in lst:
            value = ' '.join(freq) if val_type == list else str(freq)
            f.write(f'{str(word)}{delim}{value}\n')


def read_dict_from_2_columns(file, val_type=str, delim='\t'):
    words = {}
    with open(file, 'r') as f:
        for line in f:
            line = line[:-1] if line[-1] else line
            splits = line.split(delim)
            if val_type == list:
                second_column = splits[1].split(' ')
            else:
                try:
                    second_column = int(splits[1])
                except:
                    second_column = splits[1]
            words[splits[0]] = second_column
    return words


def read_list(file):
    res = []
    with open(file, 'r') as f:
        for line in f:
            line = line.rstrip('\n')
            splits = line.split(' ')
            res.append(splits if len(splits) > 1 else splits[0])
    return res


def dump_list(lst, file):
    with open(file, 'w') as f:
        for elm in lst:
            if isinstance(elm, list) or isinstance(elm, tuple):
                f.write(f"{' '.join(elm)}\n")
            else:
                f.write(f"{elm}\n")
