#!/usr/bin/env bash

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

PROJECT_ROOT="$CURRENT_DIR/.."

echo "doing cd to $PROJECT_ROOT"
cd "$PROJECT_ROOT"

echo "Running parse_projects.py ..."
python logrec/dataprep/parse_projects.py test1
echo "Showing contents of nn-data/test after parse_projects.py command:"
tree -L 2 nn-data/test
