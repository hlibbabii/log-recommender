#!/usr/bin/env bash

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

PROJECT_ROOT="$CURRENT_DIR/.."

echo "doing cd to $PROJECT_ROOT"
cd "$PROJECT_ROOT"

python logrec/dataprep/parse_projects.py test1