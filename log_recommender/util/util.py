from functools import reduce

__author__ = 'hlib'


def without_duplicates(list):
    seen = set()
    seen_add = seen.add
    return [x for x in list if not (x in seen or seen_add(x))]

def sum_vectors(vectors):
    if len(vectors) == 0:
        return [0.0, 0.0, 0.0, 0.0, 0.0]
    sum_vector = reduce(lambda x_vec, y_vec: [x + y for x,y in zip(x_vec, y_vec)], vectors)
    return [s / len(vectors) for s in sum_vector]