import argparse

__author__ = 'hlib'

import matplotlib.pyplot as plt
import pandas as pd

from sklearn.decomposition import PCA as sklearnPCA


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--autoencode-dist-file', action='store', default='../AutoenCODE/out/word2vec/word2vec.out')
    args = parser.parse_args()

    data = []
    annotations = []
    with open(args.autoencode_dist_file, 'rb') as f:
        f.readline()
        for line in f:
            split_line = line.split()
            data.append(split_line[1:])
            annotations.append(split_line[0])

    pca = sklearnPCA(n_components=2) #2-dimensional PCA
    transformed = pd.DataFrame(pca.fit_transform(data))

    fig, ax = plt.subplots()
    x = transformed[:][0]
    z = transformed[:][1]
    ax.scatter(x, z)

    for i, a in enumerate(annotations):
        ax.annotate(str(a, 'utf-8'), (x[i],z[i]))

    plt.legend()
    plt.show()