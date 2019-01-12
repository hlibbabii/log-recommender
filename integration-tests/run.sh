#!/usr/bin/env bash

set -e

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

PROJECT_ROOT="$CURRENT_DIR/.."

echo "doing cd to $PROJECT_ROOT"
cd "$PROJECT_ROOT"

function show_test_dir_contents() {
    echo "Showing contents of nn-data/test:"
    tree -L 3 nn-data/test
}

python logrec/dataprep/parse_projects.py test1
show_test_dir_contents

python logrec/dataprep/to_repr.py --preprocessing-params "enonly=1,nocomstr=0,spl=1,nosep=0,nonewlinestabs=1" test1
show_test_dir_contents

python logrec/dataprep/vocabsize.py test1 10101
show_test_dir_contents

python logrec/dataprep/split/bpe.py test1 10101 10 --reset
show_test_dir_contents

python logrec/dataprep/to_repr.py --preprocessing-params "enonly=1,nocomstr=0,spl=4,nosep=0,nonewlinestabs=1" --bpe-base-repr 10101 --bpe-n-merges 10 test1
show_test_dir_contents

python logrec/dataprep/vocabsize.py test1 10401
show_test_dir_contents

echo "Displaying vocab sizes"
wc -l "$PROJECT_ROOT/nn-data/test/test1/metadata/10101/vocab"
wc -l "$PROJECT_ROOT/nn-data/test/test1/metadata/10401/vocab"

python logrec/classifier/dataset_generator.py test1 10401 location
show_test_dir_contents

python logrec/classifier/dataset_generator.py test1 10401 level
show_test_dir_contents

python logrec/classifier/dataset_stats.py test1 10401 1.0
show_test_dir_contents

