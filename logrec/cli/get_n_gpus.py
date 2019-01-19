#!/usr/bin/env python

from logrec.util import gpu

if __name__ == '__main__':
    if gpu.gpu_available():
        print(gpu.get_n_gpus())
    else:
        print(-1)
