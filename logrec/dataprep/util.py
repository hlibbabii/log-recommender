def insert_separators(subwords, separator):
    return [s for subword in subwords for s in (subword, separator)][:-1]

def create_regex_from_token_list(token_list):
    m = list(map(lambda x:
             x.replace('\\', '\\\\')
                 .replace("^", "\\^")
                 .replace("+", "\+")
                 .replace("|", "\|")
                 .replace("*", "\*")
                 .replace("[", "\[")
                 .replace("]", "\]")
                 .replace("-", "\-")
                 .replace('"', '\\"')
                 .replace('?', "\?")
                 .replace('(', "\(")
                 .replace(')', "\)")
                 .replace(".", "\.")
                 , token_list))
    return "(" + "|".join(
        m
    ) +")"


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
