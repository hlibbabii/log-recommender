__author__ = 'hlib'


def without_duplicates(list):
    seen = set()
    seen_add = seen.add
    return [x for x in list if not (x in seen or seen_add(x))]