#!/usr/bin/env python

from logrec.util import io

__author__ = 'hlib'

if __name__ == '__main__':
    # id = sys.argv[1]
    id = "mapbox_161506"
    pp_logs_gen = io.load_preprocessed_logs()
    for log in pp_logs_gen:
        if log.id == id:
            print(log.text)
            print(log.level)
            print(log.context.context_before)
            exit(0)
    print("Id " + str(id) + " not found")
    exit(1)
