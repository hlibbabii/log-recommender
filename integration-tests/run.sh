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

python logrec/dataprep/to_repr.py --preprocessing-params 10111 test1
show_test_dir_contents

python logrec/dataprep/vocabsize.py test1 10111
show_test_dir_contents

python logrec/dataprep/split/bpe.py test1 10111 10 --reset
show_test_dir_contents

python logrec/dataprep/to_repr.py --preprocessing-params 10411 --bpe-base-repr 10111 --bpe-n-merges 10 test1
show_test_dir_contents

python logrec/dataprep/vocabsize.py test1 10411
show_test_dir_contents

echo "Displaying vocab sizes"
wc -l "$PROJECT_ROOT/nn-data/test/test1/metadata/10111/vocab"
wc -l "$PROJECT_ROOT/nn-data/test/test1/metadata/10411/vocab"

python logrec/classifier/dataset_generator.py test1 10411 location
show_test_dir_contents

python logrec/classifier/dataset_generator.py test1 10411 level
show_test_dir_contents

python logrec/classifier/dataset_stats.py test1 10411 1.0
show_test_dir_contents

