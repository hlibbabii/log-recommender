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

python logrec/dataprep/to_repr.py --preprocessing-params "enonly=1,nocomstr=0,spl=1,nosep=0,nonewlinestabs=1,nologs=0" test1
show_test_dir_contents

python logrec/dataprep/vocabsize.py test1 101010
show_test_dir_contents

cp "$PROJECT_ROOT/nn-data/test/test1/metadata/101010/vocab" "$PROJECT_ROOT/vocab"

logrec/dataprep/split/bpe.py --n-merges 10 --reset
show_test_dir_contents