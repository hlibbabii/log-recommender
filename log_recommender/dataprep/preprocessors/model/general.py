class ProcessableToken(object):
    def __init__(self, s):
        if isinstance(s, str):
            self.val = s
        else:
            raise AssertionError(f"Bad type of obj: {str}")

    def get_val(self):
        return self.val

    def to_repr(self):
        return self.val

    def get_flat_list(self):
        return self.__get_flat_list(self.val)

    def __str__(self):
        return self.val

    def __repr__(self):
        return self.__str__()

    def __get_flat_list(self, val):
        if isinstance(val, list):
            return [r for v in val for r in self.__get_flat_list(v)]
        elif isinstance(val, str):
            return val
        elif isinstance(val, ProcessableToken):
            return val.get_flat_list()
        else:
            raise AssertionError(f"Bad type of obj: {str}")

    def get_processable_subtokens(self):
        if self.simple():
            return [self]
        else:
            return [pst for st in self.val if isinstance(st, ProcessableToken) for pst in st.get_processable_subtokens()]

    def simple(self):
        return len(self.val) == 1 and isinstance(self.val[0], str)


class ProcessableTokenContainer(object):
    def __init__(self, subtokens):
        if isinstance(subtokens, list):
            self.subtokens = subtokens
        else:
            raise AssertionError(f"Should be list byt is: {subtokens}")

    def get_subtokens(self):
        return self.subtokens